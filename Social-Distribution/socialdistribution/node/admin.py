from django.contrib import admin
from .models import Author, Like, Comment, Post, Follow

# Register your models here.
admin.site.register(Author)
# admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(Post)
admin.site.register(Follow)