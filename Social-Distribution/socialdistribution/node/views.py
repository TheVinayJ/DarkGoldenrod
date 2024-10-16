from django.core import signing
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView
from .models import Post, Author, PostLike, Comment, Like, Follow
from django.contrib import messages
from django.db.models import Q
import datetime
import os

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
    author_id = get_author(request).id

    posts = []
    post_objects = Post.objects.all()
    for post in post_objects:
        posts.append({
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
    return render(request, "index.html", {
        "posts": posts,
        'author_id': author_id,
    })


def editor(request):
    return render(request, "editor.html")


def save(request):
    author = get_object_or_404(Author, get_author(request))
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
    author = get_author(request)
    post = get_object_or_404(Post, pk=id)
    if PostLike.objects.filter(owner=post, liker=author).exists():
        PostLike.objects.filter(owner=post, liker=author).delete()
    else:
        new_like = PostLike(owner=post, created_at=datetime.datetime.now(), liker=author)
        new_like.save()
    return(redirect(f'/node/posts/{id}/'))

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
    post = get_object_or_404(Post, id=post_id)
    author = get_author(request)
    liked = False

    if PostLike.objects.filter(owner=post, liker=author).exists():
        liked = True

    return render(request, "post.html", {
        "post": post,
        "id": post_id,
        'likes': PostLike.objects.filter(owner=post),
        'author': author,
        'liked' : liked,
        'author_id': author.id,
        'comments': Comment.objects.filter(post=post),
    })


def profile(request, author_id):
    user = get_object_or_404(Author, id=author_id)
    authors_posts = Post.objects.filter(author=user).order_by('-published') # most recent on top
    if authors_posts:
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
    return get_object_or_404(Author, id=request.COOKIES.get('ID', None))