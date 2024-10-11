from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView
from .models import Post, Author
from django.db.models import Q
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