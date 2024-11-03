# yourapp/serializers.py

from rest_framework import serializers
from .models import Author, RemoteNode
from django.contrib.auth import authenticate


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
    class Meta:
        model = Author
        fields = ['id','display_name', 'profile_image', 'description', 'github']