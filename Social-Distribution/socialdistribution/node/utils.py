from rest_framework.views import exception_handler
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
from rest_framework.response import Response
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from .models import RemoteNode
from requests.auth import HTTPBasicAuth
import requests

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    # Add custom claims
    refresh['user_id'] = user.id
    refresh['email'] = user.email

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def get_authenticated_user_id(request):
    """
    Returns the authenticated user's ID if the user is authenticated.
    Raises AuthenticationFailed if the user is not authenticated.
    """
    if request.user and request.user.is_authenticated:
        return request.user.id
    else:
        raise AuthenticationFailed('User is not authenticated.')

def custom_exception_handler(exc, context):
    if isinstance(exc, NotAuthenticated):
        request = context.get('request')
        # Redirect to login page with 'next' parameter
        login_url = '/node/login/?next=' + request.path
        return HttpResponseRedirect(login_url)
    # Call REST framework's default exception handler for other exceptions
    response = exception_handler(exc, context)
    return response

def send_request_to_node(node_name, endpoint, method='GET', data=None):
    '''
        Send an HTTP request to a remote node.

        Parameters:
            node_name: The name of the remote node (When we add the node to connect in admin panel, we will give it a name).
            endpoint: The endpoint to send the request to. Example: /api/posts/
            method: {GET, POST, PUT, DELETE}
            data: data for POST or PUT requests
    '''
    try:
        node = RemoteNode.objects.get(name=node_name, is_active=True)
    except RemoteNode.DoesNotExist:
        raise Exception(f"Node '{node_name}' is not active or does not exist.")

    url = f"{node.url}{endpoint}"
    auth = HTTPBasicAuth(node.username, node.password)

    if method.upper() == 'GET':
        response = requests.get(url, auth=auth)
    elif method.upper() == 'POST':
        response = requests.post(url, json=data, auth=auth)
    elif method.upper() == 'PUT':
        response = requests.put(url, json=data, auth=auth)
    elif method.upper() == 'DELETE':
        response = requests.delete(url, auth=auth)
    else:
        raise Exception(f"Unsupported HTTP method: {method}")
    return response


def post_request_to_node(host, url, method='POST', data=None):
    '''
        Send an HTTP request to a remote node.

        Parameters:
            node_name: The name of the remote node (When we add the node to connect in admin panel, we will give it a name).
            endpoint: The endpoint to send the request to. Example: /api/posts/
            method: {GET, POST, PUT, DELETE}
            data: data for POST or PUT requests
    '''
    try:
        node = RemoteNode.objects.get(url=host, is_active=True)
    except RemoteNode.DoesNotExist:
        raise Exception(f"Node '{host}' is not active or does not exist.")

    auth = HTTPBasicAuth(node.username, node.password)

    if method.upper() == 'GET':
        response = requests.get(url, auth=auth)
    elif method.upper() == 'POST':
        response = requests.post(url, json=data, auth=auth)
    elif method.upper() == 'PUT':
        response = requests.put(url, json=data, auth=auth)
    elif method.upper() == 'DELETE':
        response = requests.delete(url, auth=auth)
    else:
        raise Exception(f"Unsupported HTTP method: {method}")
    return response