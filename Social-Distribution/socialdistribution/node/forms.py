# app/forms.py
from django import forms
from .models import Image, Author

class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['image']

class AuthorProfileForm(forms.ModelForm):
    class Meta:
        model = Author  # Use your Author model
        fields = ['display_name', 'profile_image', 'description']  # Include other fields as needed
