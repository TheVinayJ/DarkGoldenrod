from email._header_value_parser import ContentType

from django.db import models
import django
import datetime


# Create your models here.
class Author(models.Model):
    id = models.AutoField(primary_key=True)
    display_name = models.CharField(max_length=50)
    description = models.CharField(max_length=150, default="")
    host = models.CharField(max_length=50) # URL of host node
    github = models.CharField(max_length=50) # URL of author's Github
    profile_image = models.CharField(max_length=100) # Link to profile picture
    page = models.CharField(max_length=100) # URL of user's HTML profile page
    friends = models.ManyToManyField('Author', blank=True)

class Like(models.Model):
    object_id = models.PositiveIntegerField()
    created_at = models.DateTimeField(default=django.utils.timezone.now)

    class Meta:
        abstract = True


class Post(models.Model):
    id = models.AutoField(primary_key=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=100)
    description = models.TextField() # Posts need a short description
    text_content = models.TextField(blank=True) # Text post content (optional)
    image_content = models.TextField(blank=True) # Link to image
    published = models.DateTimeField(auto_now_add=True)

class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    text = models.TextField()

class PostLike(Like):
    owner = models.ForeignKey(Post, on_delete=models.CASCADE)

class CommentLike(Like):
    owner = models.ForeignKey(Comment, on_delete=models.CASCADE)