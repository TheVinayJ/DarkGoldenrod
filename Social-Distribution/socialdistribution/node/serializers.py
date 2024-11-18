# yourapp/serializers.py

from rest_framework import serializers
from rest_framework.reverse import reverse
from .models import Author, RemoteNode, Post, Like, PostLike, CommentLike, Comment
import datetime
from django.contrib.auth import authenticate

class AuthorSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default='author')
    id = serializers.SerializerMethodField()
    host = serializers.SerializerMethodField()
    displayName = serializers.CharField(source='display_name')
    github = serializers.CharField()
    profileImage = serializers.SerializerMethodField()
    page = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = ['type', 'id', 'host', 'displayName', 'github', 'profileImage', 'page']

    def get_id(self, obj):
        return f"http://darkgoldenrod/api/authors/{obj.id}"

    def get_host(self, obj):
        return "http://darkgoldenrod/api"

    def get_page(self, obj):
        return f"http://darkgoldenrod/{obj.id}/profile"

    def get_profileImage(self, obj):
        if obj.profile_image:
            return obj.profile_image.url
        return None

class LikeSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default='like')
    author = AuthorSerializer(source='liker')
    object = serializers.URLField()
    published = serializers.DateTimeField(default=datetime.datetime.now)
    id = serializers.URLField()

    class Meta:
        model = PostLike  
        fields = ['type', 'author', 'object', 'published', 'id']

    # ChatGPT 4o. Nov 2024. How can I identify if a instance in a serializer is of type CommentLike or PostLike.
    def get_model_class(self):
        """Helper method to determine which model to use based on the instance"""
        if hasattr(self.instance, 'owner'):
            if hasattr(self.instance.owner, 'post'): 
                return CommentLike
            return PostLike
        return PostLike
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        model_class = self.get_model_class()
        
        if model_class == CommentLike:
            comment = instance.owner
            data['object'] = f"http://darkgoldenrod/api/authors/{comment.author.id}/posts/{comment.post.id}/comments/{comment.id}"
        else:
            post = instance.owner
            data['object'] = f"http://darkgoldenrod/api/authors/{post.author.id}/posts/{post.id}"
        
        data['id'] = f"http://darkgoldenrod/api/authors/{instance.liker.id}/liked/{instance.object_id}"
        
        return data
    
class LikesSerializer(serializers.Serializer):
    # Microsoft Copilot, Nov. 2024. Serializer for aggregate of models
    type = serializers.CharField(default='likes')
    page = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    page_number = serializers.IntegerField(default=1)
    size = serializers.IntegerField(default=50)
    count = serializers.SerializerMethodField()
    src = serializers.SerializerMethodField()

    def get_page(self, obj):
        if hasattr(obj, 'post'):  
            return f"http://darkgoldenrod/authors/{obj.post.author.id}/posts/{obj.post.id}/comments/{obj.id}"
        else:  
            return f"http://darkgoldenrod/authors/{obj.author.id}/posts/{obj.id}"

    def get_id(self, obj):
        if hasattr(obj, 'post'):  
            return f"http://darkgoldenrod/api/authors/{obj.post.author.id}/posts/{obj.post.id}/comments/{obj.id}/likes"
        else:  
            return f"http://darkgoldenrod/api/authors/{obj.author.id}/posts/{obj.id}/likes"

    def get_count(self, obj):
        if hasattr(obj, 'post'): 
            return CommentLike.objects.filter(owner=obj).count()
        else:  
            return PostLike.objects.filter(owner=obj).count()

    def get_src(self, obj):
        page_number = self.context.get('page_number', 1)
        page_size = self.context.get('size', 50)
        
        if hasattr(obj, 'post'):  
            likes = CommentLike.objects.filter(owner=obj).order_by('-created_at')
        else:  
            likes = PostLike.objects.filter(owner=obj).order_by('-created_at')
        
        start = (page_number - 1) * page_size
        end = start + page_size
        likes_subset = likes[start:end]
        
        return LikeSerializer(likes_subset, many=True).data

class CommentSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default="comment")
    author = AuthorSerializer()
    comment = serializers.CharField(source='text')
    contentType = serializers.CharField(default='text/markdown')
    published = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")
    id = serializers.SerializerMethodField()
    post = serializers.SerializerMethodField()
    likes = LikesSerializer(source='*')

    class Meta:
        model = Comment
        fields = ['type', 'author', 'comment', 'contentType', 'published', 'id', 'post', 'likes']

    def get_id(self, obj):
        return f"http://darkgoldenrod/api/authors/{obj.author.id}/commented/{obj.id}"

    def get_post(self, obj):
        return f"http://darkgoldenrod/api/authors/{obj.post.author.id}/posts/{obj.post.id}"


class CommentsSerializer(serializers.Serializer):
    # Microsoft Copilot, 2024. Aggregate of Comment serializer
    type = serializers.CharField(default="comments")
    page = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    page_number = serializers.IntegerField(default=1)
    size = serializers.IntegerField(default=5)
    count = serializers.SerializerMethodField()
    src = serializers.SerializerMethodField()

    def get_page(self, obj):
        return f"http://darkgoldenrod/authors/{obj.author.id}/posts/{obj.id}"

    def get_id(self, obj):
        return f"http://darkgoldenrod/api/authors/{obj.author.id}/posts/{obj.id}/comments"

    def get_count(self, obj):
        return  Comment.objects.filter(post=obj).count()

    def get_src(self, obj):
        comments = Comment.objects.filter(post=obj).order_by('-published')
        return CommentSerializer(comments, many=True).data

class PostSerializer(serializers.ModelSerializer):
    content = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField
    comments = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'type',
            'title',
            'id',
            'description',
            'contentType',
            'content',
            'visibility',
            'author',
            'published',
            'comments',
            'likes',
        ]

    def get_id(self, obj):
        return f"http://darkgoldenrod/api/authors/{obj.author.id}/posts/{obj.id}"

    def get_author(self, obj):
        return AuthorSerializer(obj.author).data

    def get_content(self, obj):
        if obj.contentType.startswith('text'):
            return obj.text_content
        elif obj.contentType.startswith('image'):
            return obj.image_content.url if obj.image_content else None
        return None

    def get_type(self, obj):
        return "post"

    def get_comments(self, obj):
        return CommentsSerializer(obj).data

    def get_likes(self, obj):
        return LikesSerializer(obj).data

class SignupSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = Author
        fields = (
            'id',
            'display_name',
            'email',
            'password',
            'confirm_password',
        )
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return attrs

    def create(self, validated_data, **kwargs):
        is_active = kwargs.pop('is_active', True)
        host = kwargs.pop('host', 'none')
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        author = Author(**validated_data)
        author.is_active = is_active
        author.host = host
        author.set_password(password)
        author.save()  # Ensure the author is saved to the database
        return author

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(username=email, password=password)
        if user is None:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_active:
            raise serializers.ValidationError("Your account is pending approval.")
        
        attrs['user'] = user
        return attrs

class AuthorProfileSerializer(serializers.ModelSerializer):
    description = serializers.CharField(default="", allow_blank=True)
    github = serializers.CharField(default="", allow_blank=True)
    class Meta:
        model = Author
        fields = ['id','display_name', 'profile_image', 'description', 'github']

    def update(self, instance, validated_data):
        # Get the profile_image from validated_data if it exists
        profile_image = validated_data.pop('profile_image', None)

        # If a new profile image is provided, update it; otherwise, keep the existing one
        if profile_image is not None:
            instance.profile_image = profile_image

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance