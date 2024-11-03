# app/forms.py
from django import forms
from .models import Image, Author

class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['image']

class AuthorProfileForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['display_name', 'profile_image', 'description', 'github']
