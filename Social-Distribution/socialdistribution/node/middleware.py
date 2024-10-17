# yourapp/middleware.py

from django.shortcuts import redirect
from django.core import signing
from django.conf import settings
from django.urls import reverse
from .models import Author

class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Define the paths that do not require authentication
        self.allowed_paths = [
            reverse('login'),
            reverse('signup'),
        ]

    def __call__(self, request):
        if any(request.path.startswith(path) for path in self.allowed_paths):
            return self.get_response(request)

        signed_user_id = request.COOKIES.get('id')
        if signed_user_id:
            try:
                user_id = signing.loads(signed_user_id)
                author = Author.objects.get(id=user_id)
                request.author = author
            except (signing.BadSignature, Author.DoesNotExist):
                response = redirect('login')
                response.delete_cookie('id')
                return response
        else:
            return redirect('login')

        response = self.get_response(request)
        return response