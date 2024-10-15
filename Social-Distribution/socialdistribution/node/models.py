from email._header_value_parser import ContentType
from django.db import models
import django
import datetime

class Author(models.Model):
    id = models.AutoField(primary_key=True)
    display_name = models.CharField(max_length=50)
    description = models.CharField(max_length=150, default="", blank=True, null=True)
    host = models.CharField(max_length=50, blank=True, null=True) # URL of host node
    github = models.CharField(max_length=50, blank=True, null=True) # URL of author's Github
    profile_image = models.CharField(max_length=100, blank=True, null=True) # Link to profile picture
    page = models.CharField(max_length=100, blank=True, null=True) # URL of user's HTML profile page
    friends = models.ManyToManyField('Author', blank=True)
    password = models.CharField(max_length=50, default="")
    email = models.EmailField(max_length=50, default='example@example.com')
    

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
    visibility = models.CharField(choices=(("PUBLIC", "PUBLIC"),("FRIENDS", "FRIENDS"), ("DELETED", "DELETED"), ("UNLISTED", "UNLISTED")), default="PUBLIC", max_length=50)


class Repost(Post):
    shared_by = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True)

class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    text = models.TextField()

class PostLike(Like):
    owner = models.ForeignKey(Post, on_delete=models.CASCADE)

class CommentLike(Like):
    owner = models.ForeignKey(Comment, on_delete=models.CASCADE)

class Follow(models.Model):
    follower = models.CharField(max_length=200)  # Full URL of the follower author
    following = models.CharField(max_length=200)  # Full URL of the author being followed
    approved = models.BooleanField(default=False)  # To track if the follow request is approved
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')  # Prevent duplicate follow entries

    def is_friend(self):
        # Check if the following author follows back the follower
        return Follow.objects.filter(follower=self.following, following=self.follower, approved=True).exists()