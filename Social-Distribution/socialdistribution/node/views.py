from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import Post, Author
import datetime

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
            "likes": post.likes,
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