from rest_framework.views import exception_handler
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
from rest_framework.response import Response
from django.http import HttpResponseRedirect
from django.shortcuts import redirect

# This function was generated from OpenAI, ChatGPT o1-preview
# Prompt: 'Can you make a function to get the tokens for a user?'
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    # Add custom claims
    refresh['user_id'] = user.id
    refresh['email'] = user.email

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

# This function was generated from OpenAI, ChatGPT o1-preview
# Prompt: 'Can you make a function to get the authenticated user id? If not authenticated, raise an exception and redirect to the login page.'
def get_authenticated_user_id(request):
    """
    Returns the authenticated user's ID if the user is authenticated.
    Raises AuthenticationFailed if the user is not authenticated.
    """
    if request.user and request.user.is_authenticated:
        return request.user.id
    else:
        raise AuthenticationFailed('User is not authenticated.')

# This function was generated from OpenAI, ChatGPT o1-preview
# Prompt: 'Can you make a function to get the authenticated user id? If not authenticated, raise an exception and redirect to the login page.'
def custom_exception_handler(exc, context):
    if isinstance(exc, NotAuthenticated):
        request = context.get('request')
        # Redirect to login page with 'next' parameter
        login_url = '/node/login/?next=' + request.path
        return HttpResponseRedirect(login_url)
    # Call REST framework's default exception handler for other exceptions
    response = exception_handler(exc, context)
    return response