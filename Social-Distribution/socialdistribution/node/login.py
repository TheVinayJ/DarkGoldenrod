from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Author
from django.core import signing
import hashlib

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        try:
            author = Author.objects.get(email=email, password=hashed_password)
            response = redirect('index')
            signed_id = signing.dumps(author.id)
            response.set_cookie('id', signed_id, httponly=True)
            return response
        except Author.DoesNotExist:
            return render(request, 'login/login.html', {'error': 'Invalid login credentials'})
    else:
        return render(request, 'login/login.html')

def signup(request):
    if request.method == 'POST':
        display_name = request.POST.get('display_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not all([display_name, email, password, confirm_password]):
            return render(request, 'login/signup.html', {'error': 'All fields are required.'})

        if password != confirm_password:
            return render(request, 'login/signup.html', {'error': 'Passwords do not match'})
        else:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            # Check if the email is already registered
            if Author.objects.filter(email=email).exists():
                return render(request, 'login/signup.html', {'error': 'Email is already registered'})

            # Create the Author instance
            author = Author(
                display_name=display_name,
                email=email,
                password=hashed_password
            )
            author.save()

            response = redirect('index')
            signed_id = signing.dumps(author.id)
            response.set_cookie('id', signed_id, httponly=True)
            return response
    else:
        return render(request, 'login/signup.html')