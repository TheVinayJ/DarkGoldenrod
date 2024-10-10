from email._header_value_parser import ContentType

from django.db import models


# Create your models here.
class Author(models.Model):
    id = models.AutoField(primary_key=True)
    display_name = models.CharField(max_length=50)
    host = models.CharField(max_length=50) # URL of host node
    github = models.CharField(max_length=50) # URL of author's Github
    profile_image = models.CharField(max_length=100) # Link to profile picture
    page = models.CharField(max_length=100) # URL of user's HTML profile page
    friends = models.ManyToManyField('Author')

class Like(models.Model):
    object_id = models.PositiveIntegerField()

    class Meta:
        abstract = True

class PostLike(Like):
    owner = models.ForeignKey(Post, on_delete=models.CASCADE)

class CommentLike(Like):
    owner = models.ForeignKey(Comment, on_delete=models.CASCADE)

class Post(models.Model):
    id = models.AutoField(primary_key=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField() # Posts need a short description
    text_content = models.TextField() # Text post content (optional)
    image_content = models.TextField() # Link to image
    published = models.DateTimeField(auto_now_add=True)

class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    text = models.TextField()
