from django.core import signing
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView
from .models import Post, Author, PostLike, Comment, Like, Follow, CommentLike
from django.contrib import messages
from django.db.models import Q, Count, Exists, OuterRef, Subquery
import datetime
import os
from .forms import AuthorProfileForm
from django.core.paginator import Paginator
from .forms import ImageUploadForm

class AuthorListView(ListView):
    model = Author
    template_name = 'authors.html'  # Specify the template to use
    context_object_name = 'authors'  # Name of the context object to access in the template

    # Get the query of the GET request
    def get_queryset(self):
        # Get the base queryset (all authors)
        queryset = Author.objects.all()

        # Get the search query and field
        query = self.request.GET.get('q')
        field = self.request.GET.get('field')

        # If no query is provided, return all authors
        if not query:
            return queryset

        # Perform filtering based on the field provided
        if field:
            # If a specific field is provided, filter by that field
            if field == "display_name":
                queryset = queryset.filter(display_name__icontains=query)
            elif field == "host":
                queryset = queryset.filter(host__icontains=query)
            elif field == "github":
                queryset = queryset.filter(github__icontains=query)
            elif field == "profile_image":
                queryset = queryset.filter(profile_image__icontains=query)
            elif field == "page":
                queryset = queryset.filter(page__icontains=query)
            else:
                # Return an empty queryset if the field is invalid
                queryset = Author.objects.none()
        else:
            # If no specific field is provided, search across all relevant fields
            queryset = queryset.filter(
                Q(display_name__icontains=query) |
                Q(host__icontains=query) |
                Q(github__icontains=query) |
                Q(profile_image__icontains=query) |
                Q(page__icontains=query)
            )
        
        return queryset


def editor(request):
    """
    Open menu to edit contents for a post request
    """
    return render(request, "editor.html")


def save(request):
    """
    Create a new post!
    """
    author = get_author(request)
    print(request.POST)
    post = Post(title=request.POST["title"],
                description=request.POST["body-text"],
                visibility=request.POST["visibility"],
                published=datetime.datetime.now(),
                author=author,
    )
    post.save()
    return(redirect('/node/'))


def post_like(request, id):
    """
    Method for liking a post given an ID
    If already liked by requesting author, unlike
    """
    author = get_author(request)
    post = get_object_or_404(Post, pk=id)
    if PostLike.objects.filter(owner=post, liker=author).exists():
        PostLike.objects.filter(owner=post, liker=author).delete()
    else:
        new_like = PostLike(owner=post, created_at=datetime.datetime.now(), liker=author)
        new_like.save()
    return(redirect(f'/node/posts/{id}/'))

def comment_like(request, id):
    """
    Method for liking a comment given comment ID
    if already liked by requesting author, removes the like
    """
    author = get_author(request)
    comment = get_object_or_404(Comment, pk=id)
    post = get_object_or_404(Post, pk=comment.post.id)
    if CommentLike.objects.filter(owner=comment, liker=author).exists():
        CommentLike.objects.filter(owner=comment, liker=author).delete()
    else:
        new_like = CommentLike(owner=comment, created_at=datetime.datetime.now(), liker=author)
        new_like.save()
    return(redirect(f'/node/posts/{post.id}/'))

def add_comment(request, id):
    """
    Add a comment to a question
    Get question from ID, fill out model details with request,
    save model, go to results page
    """
    if request.method != "POST":
        return HttpResponse(status=400)
    post = get_object_or_404(Post, pk=id)

    # Get request contents
    author = get_author(request)
    text = request.POST["content"]


    new_comment = Comment(post=post, text=text, author=author)
    new_comment.save()
    # Return to question
    return(redirect(f'/node/posts/{id}/'))


def view_post(request, post_id):
    """
    For viewing a post
    Returns 403 for visibility conflicts
    Otherwise, render the post
    """

    post = get_object_or_404(Post, id=post_id)
    author = get_author(request)
    liked = False

    if post.visibility == "FRIENDS":
        try:
            follow = get_object_or_404(Follow, follower=author, following = post.author)
        except:
            return HttpResponse(status=403)
        if follow.is_friend():
            return HttpResponse(status=403)

    if post.visibility == "PRIVATE":
        if post.author != author:
            return HttpResponse(status=403)

    if PostLike.objects.filter(owner=post, liker=author).exists():
        liked = True

    # user_likes strategy obtained from Microsoft Copilot, Oct. 2024
    # Find likes from current user matching the queried comment
    user_likes = CommentLike.objects.filter(owner=OuterRef('pk'), liker=author)

    return render(request, "post.html", {
        "post": post,
        "id": post_id,
        'likes': PostLike.objects.filter(owner=post),
        'author': author,
        'liked' : liked,
        'author_id': author.id,
        'comments': Comment.objects.filter(post=post)
                  .annotate(likes=Count('commentlike'),
                            liked=Exists(user_likes)
                            ),
    })


def profile(request, author_id):
    user = get_object_or_404(Author, id=author_id)
    authors_posts = Post.objects.filter(author=user).order_by('-published') # most recent on top
    return render(request, "profile.html", {
        'user': user,
        'posts': authors_posts,
    })


def edit_profile(request, author_id):
    user = get_object_or_404(Author, id=author_id)

    if request.method == 'POST':
        form = AuthorProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()  # Save the form data
            return redirect('profile', author_id=user.id)  # Redirect to the profile view after saving
    else:
        form = AuthorProfileForm(instance=user)
    return render(request, 'edit_profile.html', {'form': form, 'user': user})


def followers(request, author_id):
    user = get_object_or_404(Author, id=author_id)
    followers = user.friends.all()
    return render(request, 'authors.html', {'authors':followers})# come back to latererer


def get_author(request):
    try:
        author_id_signed = request.COOKIES.get('id')
        author_id = signing.loads(author_id_signed)
        author = Author.objects.get(id=author_id)
        return author
    except (Author.DoesNotExist, signing.BadSignature, TypeError):
        return None


def follow_author(request, author_id):
    # Get the author being followed
    author_to_follow = get_object_or_404(Author, id=author_id).id
    
    # Get the logged-in author (assuming you have a user to author mapping)
    current_author = get_author(request).id # Adjust this line to match your user-author mapping

    # Check if the follow relationship already exists
    follow_exists = Follow.objects.filter(follower="http://darkgoldenrod/api/authors/" + str(current_author), following="http://darkgoldenrod/api/authors/" + str(author_to_follow)).exists()

    if not follow_exists:
        # Create a new follow relationship
        Follow.objects.create(follower="http://darkgoldenrod/api/authors/" + str(current_author), following="http://darkgoldenrod/api/authors/" + str(author_to_follow))
        messages.success(request, "You sucessfully followed this author.")
    else:
        print("No follow relationship exists between these authors.")
        messages.warning(request, "You already followed this author.")

    # Redirect back to the authors list or a success page
    return redirect('authors')


def unfollow_author(request, author_id):
    # Get the author being followed
    author_to_unfollow = get_object_or_404(Author, id=author_id).id
    
    # Get the logged-in author (assuming you have a user to author mapping)
    current_author = get_author(request).id # Adjust this line to match your user-author mapping

    # Check if the follow relationship already exists
    follow_exists = Follow.objects.filter(follower="http://darkgoldenrod/api/authors/" + str(current_author), following="http://darkgoldenrod/api/authors/" + str(author_to_unfollow)).exists()

    if follow_exists:
        # Create a new follow relationship
        follow = get_object_or_404(Follow, follower="http://darkgoldenrod/api/authors/" + str(current_author), following="http://darkgoldenrod/api/authors/" + str(author_to_unfollow))
        # Delete the Follow object to unfollow the author
        follow.delete()
        messages.success(request, "You have successfully unfollowed this author.")

    if not follow_exists:
        # Create a new follow relationship
        print("No follow relationship exists between these authors.")
        messages.warning(request, "You are not following this author.")

    # Redirect back to the authors list or a success page
    return redirect('authors')


### WARNING: Only works for posts from authors of the same node right now
# Shows posts from followings and friends
def display_feed(request):
    """
    Display posts from the authors the logged-in user is following.
    """
    # Get the current user's full author URL
    current_author = get_author(request).id

    public_posts = Post.objects.filter(visibility="PUBLIC")

    # Get the authors that the current user is following
    follow_objects = Follow.objects.filter(follower="http://darkgoldenrod/api/authors/" + str(current_author), approved=True)

    followings = list(follow_objects.values_list('following', flat=True))
    cleaned_followings = [int(url.replace('http://darkgoldenrod/api/authors/', '')) for url in followings]

    friends = [follow.following for follow in follow_objects if follow.is_friend()]
    cleaned_friends = [int(url.replace('http://darkgoldenrod/api/authors/', '')) for url in friends]

    print(f"Current Author ID: {current_author}|")  # Debug the current author's ID
    follower_url = "http://darkgoldenrod/api/authors/" + str(current_author)
    print(f"Follower URL: {follower_url}|")  # Debug the full follower URL
    print(f'Author IDs: {followings}|')
    print(f"Cleaned Author IDs: {cleaned_followings}|")
    print(f"{public_posts}")

    # Retrieve posts from authors the user is following
    follow_posts = Post.objects.filter(author__in=cleaned_followings, visibility__in=['PUBLIC', 'UNLISTED'])

    friend_posts = Post.objects.filter(author__in=cleaned_friends, visibility__in=['FRIENDS'])
    
    posts = (public_posts | follow_posts | friend_posts).distinct().order_by('published')

    cleaned_posts = []
    for post in posts:
        cleaned_posts.append({
            "id": post.id,
            "title": post.title,
            "description": post.description,
            "author": post.author,
            "published": post.published,
            "text_content": post.text_content,
            "likes": PostLike.objects.filter(owner=post).count(),
            "comments": Comment.objects.filter(post=post).count(),
            "url": reverse("view_post", kwargs={"post_id": post.id})
        })

    # likes = [PostLike.objects.filter(owner=post).count() for post in posts]

    # Pagination setup
    paginator = Paginator(cleaned_posts, 10)  # Show 10 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    # Render the feed template and pass the posts as context
    return render(request, 'feed.html', {'page_obj': page_obj, 'author_id': current_author,})

def upload_image(request):
    signed_id = request.COOKIES.get('id')
    id = signing.loads(signed_id)
    author = get_object_or_404(Author, id=id)

    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.author = author
            image.save()
            return redirect('index')
    else:
        form = ImageUploadForm()
    return render(request, 'node_admin/upload_image.html', {'form': form})