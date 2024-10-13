from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from .models import Author
from django.contrib.auth.hashers import make_password, check_password

def email_input_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            author = Author.objects.get(email=email)
            # Email exists, redirect to login page with display_name prefilled
            return redirect(reverse('login_with_display_name') + f'?display_name={author.display_name}')
        except Author.DoesNotExist:
            # Email doesn't exist, redirect to sign-up page
            return redirect('signup')
    return render(request, 'login/email_input.html')


def login_with_display_name_view(request):
    display_name = request.GET.get('display_name', '')
    error = None
    if request.method == 'POST':
        password = request.POST.get('password')
        try:
            author = Author.objects.get(display_name=display_name)
            if check_password(password, author.password):
                # Password is correct
                request.session['author_id'] = author.id
                request.session['display_name'] = author.display_name
                return HttpResponse(f"Welcome back, {author.display_name}!")
            else:
                error = 'Invalid password'
        except Author.DoesNotExist:
            error = 'User does not exist'
    return render(request, 'login/login_page.html', {'display_name': display_name, 'error': error})


def signup_view(request):
    if request.method == 'POST':
        display_name = request.POST.get('display_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        description = request.POST.get('description', '')
        
        # Check if display_name or email already exists
        if Author.objects.filter(display_name=display_name).exists():
            error = 'Display name already taken'
            return render(request, 'signup_page.html', {'error': error})
        if Author.objects.filter(email=email).exists():
            error = 'Email already registered'
            return render(request, 'login/signup_page.html', {'error': error})
        
        # Hash the password
        hashed_password = make_password(password)
        
        # Create new Author
        author = Author.objects.create(
            display_name=display_name,
            email=email,
            password=hashed_password,
            description=description
        )
        
        # Login the user (you may set session data here)
        request.session['author_id'] = author.id
        request.session['display_name'] = author.display_name
        return HttpResponse(f"Account created for {author.display_name}!")
    return render(request, 'login/signup_page.html')