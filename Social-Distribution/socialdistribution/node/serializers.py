# yourapp/serializers.py

from rest_framework import serializers
from rest_framework.reverse import reverse

from .models import Author, RemoteNode, Post
from django.contrib.auth import authenticate

class AuthorSerializer(serializers.ModelSerializer):

    type = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    host = serializers.SerializerMethodField()
    displayName = serializers.CharField(source='display_name')
    page = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = [
            'github',
            'profileImage',
            'displayName',
        ]

    def get_type(self, obj):
        return "author"

    def get_id(self, obj):
        return f"http://darkgoldenrod/api/authors/{obj.id}"

    def get_host(self, obj):
        return "http://darkgoldenrod/api"

    def get_page(self, obj):
        return f"http://darkgoldenrod/{obj.id}/profile"

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

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        author = Author(**validated_data)
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