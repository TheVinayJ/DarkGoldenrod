from email._header_value_parser import ContentType
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from encrypted_model_fields.fields import EncryptedCharField
from django.core.validators import URLValidator
from solo.models import SingletonModel
import django
import datetime
import uuid

class AuthorManager(BaseUserManager):
    def create_user(self, email, display_name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not display_name:
            raise ValueError('The Display Name field must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, display_name=display_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, display_name, password=None, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_admin') is not True:
            raise ValueError('Superuser must have is_admin=True.')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, display_name, password, **extra_fields)


class Author(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    url = models.TextField(unique=True, null=True, default=None)
    display_name = models.CharField(max_length=255, null=False)
    email = models.EmailField(max_length=255, unique=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    host = models.CharField(max_length=255, blank=True, null=True, default='http://darkgoldenrod/api/')
    github = models.CharField(max_length=255, blank=True, null=True, default="")
    profile_image = models.ImageField(upload_to='images/profilePictures', blank=True, null=True, default="")
    page = models.TextField(blank=True, null=True)
    friends = models.ManyToManyField('self', blank=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = AuthorManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['display_name']
        
    def save(self, *args, **kwargs):
        if not self.email and self._state.adding:
            super().save(*args, **kwargs)
            self.email = f"{self.id}@foreignnode.com"
            super().save(update_fields=['email'])
        elif not self.url and self._state.adding:
            super().save(*args, **kwargs)
            self.url = f"{self.host}authors/{self.id}"
            self.page = f"{self.host[:-4]}author/{self.id}"
            super().save(update_fields=['url'])
        elif not self.url and not self.email and self._state.adding:
            super().save(*args, **kwargs)
            self.url = f"{self.host}authors/{self.id}"
            self.email = f"{self.id}@foreignnode.com"
            self.page = f"{self.host[:-4]}author/{self.id}"
            super().save(update_fields=['url', 'email'])
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name
    

class Like(models.Model):
    object_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = models.DateTimeField(default=django.utils.timezone.now, db_index=True)
    liker = models.ForeignKey(Author, on_delete=models.CASCADE, null=True)

    class Meta:
        abstract = True


class Post(models.Model):
    VISIBILITY_CHOICES = [
        ('PUBLIC', 'Public'),
        ('FRIENDS', 'Friends'),
        ('UNLISTED', 'Unlisted'),
        ('DELETED', 'Deleted'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    contentType = models.CharField(max_length=50, default="text/plain")
    text_content = models.TextField(blank=True, null=True)
    image_content = models.ImageField(upload_to='images/postImages', default=None, blank=True, null=True)
    published = models.DateTimeField()
    visibility = models.CharField(
        max_length=50,
        choices=VISIBILITY_CHOICES,
        default='PUBLIC',
    )
    url = models.URLField(max_length=255, blank=True, null=True)


class Repost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    original_post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True)
    shared_by = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True)
    shared_date = models.DateTimeField(auto_now_add=True)

class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    published = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    text = models.TextField()

class PostLike(Like):
    owner = models.ForeignKey(Post, on_delete=models.CASCADE)

class CommentLike(Like):
    owner = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True)
    
class Image(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/')
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)

class Follow(models.Model):
    follower = models.CharField(max_length=200)
    following = models.CharField(max_length=200)
    approved = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def is_friend(self):
        return Follow.objects.filter(follower=self.following, following=self.follower, approved=True).exists()

class AllowedNode(models.Model):
    url = models.URLField(unique=True)
    username = models.CharField(max_length=150)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def check_password(self, raw_password):
        return self.password == raw_password

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def groups(self):
        return []

    @property
    def user_permissions(self):
        return []
    
    def __str__(self):
        return self.url
    
class RemoteNode(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Friendly name for the remote node")
    url = models.URLField(max_length=200, validators=[URLValidator()], help_text="URL of the remote node")
    username = models.CharField(max_length=150, help_text="Username for authentication")
    password = models.CharField(max_length=128, help_text="Password for authentication")  # Now stored as plain text
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def check_password_custom(self, raw_password):
        return self.password == raw_password

    def __str__(self):
        return self.name
    
class SiteSetting(SingletonModel):
    user_approval_required = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Site Setting"

    def __str__(self):
        return "Site Settings"