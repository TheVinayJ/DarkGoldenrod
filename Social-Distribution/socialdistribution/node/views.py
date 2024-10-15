from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.core import signing
from .models import Post, Author, Follow
import datetime

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


def index(request):
    posts = []

    post_objects = Post.objects.all()
    for post in post_objects:
        posts.append({
            "id": post.id,
            "title": post.title,
            "description": post.description,
            "author": post.author,
            "text_content": post.text_content,
            # "likes": post.likes,
            "url": reverse("view_post", kwargs={"post_id": post.id})
        })
    return render(request, "index.html", {"posts": posts})

def editor(request):
    return render(request, "editor.html")

def save(request):
    post = Post(title=request.POST["title"],
                description=request.POST["body-text"],
                published=datetime.datetime.now(),
    )
    post.save()
    return(redirect('/node/'))

def view_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    return render(request, "post.html", {
        "post": post,
    })

def profile(request, user_id):
    user = get_object_or_404(Author, id=user_id)
    return render(request, "profile.html", {'user': user})

def get_author(request):
    return get_object_or_404(Author, id=signing.loads(request.COOKIES.get('id', None)))

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
def display_feed(request):
    """
    Display posts from the authors the logged-in user is following.
    """
    # Get the current user's full author URL
    current_author = get_author(request).id

    # Get the authors that the current user is following
    followings = list(Follow.objects.filter(follower="http://darkgoldenrod/api/authors/" + str(current_author), approved=True).values_list('following', flat=True))

    cleaned_followings = [int(url.replace('http://darkgoldenrod/api/authors/', '')) for url in followings]

    print(f"Current Author ID: {current_author}|")  # Debug the current author's ID
    follower_url = "http://darkgoldenrod/api/authors/" + str(current_author)
    print(f"Follower URL: {follower_url}|")  # Debug the full follower URL
    print(f'Author IDs: {followings}|')
    print(f"Cleaned Author IDs: {cleaned_followings}|")

    # Retrieve posts from authors the user is following
    posts = Post.objects.filter(author__in=cleaned_followings).order_by('published')

    # Pagination setup
    paginator = Paginator(posts, 10)  # Show 10 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Render the feed template and pass the posts as context
    return render(request, 'feed.html', {'page_obj': page_obj})