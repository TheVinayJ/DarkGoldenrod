# app/forms.py
from django import forms
from .models import Image, Author, Post

class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['image']

class AuthorProfileForm(forms.ModelForm):
    class Meta:
        model = Author  # Use your Author model
        fields = ['display_name', 'description']

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'description',]  # Add other fields as necessary
