# yourapp/serializers.py
import base64
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
    github = serializers.CharField(allow_null=True,allow_blank=True)
    profileImage = serializers.SerializerMethodField()
    page = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = ['type', 'id', 'host', 'displayName', 'github', 'profileImage', 'page']

    def get_id(self, obj):
        return obj.url

    def get_host(self, obj):
        return obj.host

    def get_page(self, obj):
        return obj.url

    def get_profileImage(self, obj):
        if obj.profile_image:
            return obj.profile_image.url
        return None

# class PostLikeSerializer(serializers.ModelSerializer):
#     type = serializers.CharField(default='like')
#     author = AuthorSerializer()
#     object = serializers.SerializerMethodField()
#     published = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")
#     id = serializers.SerializerMethodField()

#     class Meta:
#         model = PostLike  
#         fields = ['type', 'author', 'object', 'published', 'id']
    
#     def get_id(self, obj):
#         return f"{obj.host}authors/{obj.author.id}/liked/{obj.id}"
    
#     def get_object(self, obj):
#         return f"{obj.host}authors/{obj.owner.author.id}/posts/{obj.owner.id}"
    
class CommentLikeSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default='like')
    author = AuthorSerializer()
    object = serializers.SerializerMethodField()
    published = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")
    id = serializers.SerializerMethodField()

    class Meta:
        model = CommentLike
        fields = ['type', 'author', 'object', 'published', 'id']

    def get_id(self, obj):
        return f"{obj.liker.host}authors/{obj.liker.id}/liked/{obj.object_id}"

    def get_object(self, obj):
        return f"{obj.liker.host}authors/{obj.owner.post.author.id}/posts/{obj.owner.post.id}/comments/{obj.owner.id}"
    
    
class PostLikesSerializer(serializers.Serializer):
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
            return f"{obj.author.host}authors/{obj.author.id}/posts/{obj.id}/comments/{obj.id}"
        else:  
            return f"{obj.author.host}authors/{obj.author.id}/posts/{obj.id}"

    def get_id(self, obj):
        if hasattr(obj, 'post'):  
            return f"{obj.author.host}authors/{obj.author.id}/posts/{obj.id}/comments/{obj.id}/likes"
        else:  
            return f"{obj.author.host}authors/{obj.author.id}/posts/{obj.id}/likes"

    def get_count(self, obj):
        return  PostLike.objects.filter(owner=obj).count()

    def get_src(self, obj):
        page_number = self.context.get('page_number', 1)
        page_size = self.context.get('size', 50)

        likes = PostLike.objects.filter(owner=obj).order_by('-created_at')

        start = (page_number - 1) * page_size
        end = start + page_size
        query_likes = likes[start:end]
        return PostLikeSerializer(query_likes, many=True).data

class PostLikeSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default='like')
    author = AuthorSerializer(source='liker')
    object = serializers.SerializerMethodField()
    published = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")
    id = serializers.SerializerMethodField()

    class Meta:
        model = PostLike
        fields = ['type', 'author', 'object', 'published', 'id']
    
    def get_id(self, obj):
        return f"{obj.liker.host}authors/{obj.liker.id}/liked/{obj.object_id}"
    
    def get_object(self, obj):
        return f"{obj.owner.author.host}authors/{obj.owner.author.id}/posts/{obj.owner.id}"
    
    
class CommentLikesSerializer(serializers.Serializer):
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
            return f"{obj.author.host}authors/{obj.post.author.id}/posts/{obj.post.id}/comments/{obj.id}"
        else:  
            return f"{obj.post.author.host}authors/{obj.author.id}/posts/{obj.id}"

    def get_id(self, obj):
        if hasattr(obj, 'post'):  
            return f"{obj.post.author.host}authors/{obj.post.author.id}/posts/{obj.post.id}/comments/{obj.id}/likes"
        else:  
            return f"{obj.post.author.host}authors/{obj.author.id}/posts/{obj.id}/likes"

    def get_count(self, obj):
        return  CommentLike.objects.filter(owner=obj).count()

    def get_src(self, obj):
        page_number = self.context.get('page_number', 1)
        page_size = self.context.get('size', 50)

        likes = CommentLike.objects.filter(owner=obj).order_by('-created_at')

        start = (page_number - 1) * page_size
        end = start + page_size
        query_likes = likes[start:end]
        return CommentLikeSerializer(query_likes, many=True).data

class CommentSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default="comment")
    author = AuthorSerializer()
    comment = serializers.CharField(source='text')
    contentType = serializers.CharField(default='text/markdown')
    published = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")
    id = serializers.SerializerMethodField()
    post = serializers.SerializerMethodField()
    likes = CommentLikesSerializer(source='*', required=False)

    class Meta:
        model = Comment
        fields = ['type', 'author', 'comment', 'contentType', 'published', 'id', 'post', 'likes']

    def get_id(self, obj):
        return f"{obj.post.author.host}authors/{obj.author.id}/commented/{obj.id}"

    def get_post(self, obj):
        return f"{obj.post.author.host}authors/{obj.post.author.id}/posts/{obj.post.id}"


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
        return f"{obj.author.host}authors/{obj.author.id}/posts/{obj.id}"

    def get_id(self, obj):
        return f"{obj.author.host}authors/{obj.author.id}/posts/{obj.id}/comments"

    def get_count(self, obj):
        return  Comment.objects.filter(post=obj).count()

    def get_src(self, obj):
        comments = Comment.objects.filter(post=obj).order_by('-published')
        return CommentSerializer(comments, many=True).data

class PostSerializer(serializers.ModelSerializer):
    content = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    #author = serializers.SerializerMethodField()
    author = AuthorSerializer()
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
            'url',
            'published',
            'comments',
            'likes',
        ]

    # def get_id(self, obj):
    #     return f"{obj.author.host}authors/{obj.author.id}/posts/{obj.id}"

    # def get_author(self, obj):
    #     if isinstance(obj.author, Author):
    #         return AuthorSerializer(obj.author).data
    #     else:
    #         author = Author.objects.filter(url=obj.author.id).first()
    #         return AuthorSerializer(author).data
        
    def get_id(self, obj):
        # Use the post's URL if it's from a remote node; otherwise, generate it dynamically
        if obj.url:
            return obj.url
        return f"{obj.author.host}authors/{obj.author.id}/posts/{obj.id}"

    def get_url(self, obj):
        # If the URL exists in the model, use it; otherwise, generate it dynamically
        if obj.url:
            return obj.url
        return f"{obj.author.host}authors/{obj.author.id}/posts/{obj.id}"

    def get_content(self, obj):
        if obj.contentType.startswith('text'):
            return obj.text_content
        elif obj.contentType.startswith('image') and obj.image_content:
            # Read the file and encode it to base64
            with obj.image_content.open('rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        return None

    def get_type(self, obj):
        return "post"

    def get_comments(self, obj):
        return CommentsSerializer(obj).data

    def get_likes(self, obj):
        return PostLikesSerializer(obj).data

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

    def save(self, **kwargs):
        return self.create(self.validated_data, **kwargs)

    def create(self, validated_data, **kwargs):
        is_active = kwargs.pop('is_active', True)
        host = kwargs.pop('host', 'None')
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')

        # Add host to validated_data
        validated_data['host'] = host

        author = Author(**validated_data)
        author.is_active = is_active
        #author.host = host
        author.set_password(password)
        author.save()
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