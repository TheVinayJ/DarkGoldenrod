from django import forms
from .models import Author  # Adjust based on your model location

class AuthorProfileForm(forms.ModelForm):
    class Meta:
        model = Author  # Use your Author model
        fields = ['display_name', 'profile_image', 'description']  # Include other fields as needed