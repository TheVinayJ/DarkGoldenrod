from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView
from .models import Post, Author
import datetime

class AuthorListView(ListView):
    model = Author
    template_name = 'authors.html'  # Specify the template to use
    context_object_name = 'authors'  # Name of the context object to access in the template

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
                # Needs author field!
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