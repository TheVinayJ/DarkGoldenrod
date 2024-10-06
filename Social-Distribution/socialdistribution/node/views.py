from django.shortcuts import render
from django.urls import reverse
from.models import Post

# Index taken from Lab 2
# Needs to be changed, just using for testing purposes
def index(request):
    posts = []

    post_objects = Post.objects.all()
    for post in post_objects:
        posts.append({
            "title": post.title,
            "url": reverse("view", kwargs={ "id": post.id })
        })
    return render(request, "index.html", { "posts": posts })

def editor(request):
    return render(request, "editor.html")