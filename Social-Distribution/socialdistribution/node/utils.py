from rest_framework.views import exception_handler
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
from rest_framework.response import Response
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from .models import RemoteNode
from requests.auth import HTTPBasicAuth
import requests
import aiohttp
from asgiref.sync import sync_to_async
from django.db import connections

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

# def send_request_to_node(node_name, endpoint, method='GET', data=None):
#     '''
#         Send an HTTP request to a remote node.

#         Parameters:
#             node_name: The name of the remote node (When we add the node to connect in admin panel, we will give it a name).
#             endpoint: The endpoint to send the request to. Example: /api/posts/
#             method: {GET, POST, PUT, DELETE}
#             data: data for POST or PUT requests
#     '''
#     try:
#         node = RemoteNode.objects.get(name=node_name, is_active=True)
#     except RemoteNode.DoesNotExist:
#         raise Exception(f"Node '{node_name}' is not active or does not exist.")

#     url = f"{node.url}{endpoint}"
#     auth = HTTPBasicAuth(node.username, node.password)

#     if method.upper() == 'GET':
#         response = requests.get(url, auth=auth)
#     elif method.upper() == 'POST':
#         response = requests.post(url, json=data, auth=auth)
#     elif method.upper() == 'PUT':
#         response = requests.put(url, json=data, auth=auth)
#     elif method.upper() == 'DELETE':
#         response = requests.delete(url, auth=auth)
#     else:
#         raise Exception(f"Unsupported HTTP method: {method}")
#     return response


def post_request_to_node(host, url, method='POST', data=None):
    '''
        Send an HTTP request to a remote node.

        Parameters:
            node_name: The name of the remote node (When we add the node to connect in admin panel, we will give it a name).
            endpoint: The endpoint to send the request to. Example: /api/posts/
            method: {GET, POST, PUT, DELETE}
            data: data for POST or PUT requests
    '''

    node = RemoteNode.objects.filter(url=host, is_active=True).first()

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

# Asynchronous function to send requests to nodes
async def send_request_to_node(node_name, endpoint, method='GET', data=None):
    '''
    Send an asynchronous HTTP request to a remote node.

    Parameters:
        node_name: The name of the remote node.
        endpoint: The endpoint to send the request to. Example: /api/posts/
        method: {GET, POST, PUT, DELETE}
        data: data for POST or PUT requests
    '''
    # Close any existing database connections to prevent errors in async context
    connections.close_all()

    try:
        node = await sync_to_async(RemoteNode.objects.get)(name=node_name, is_active=True)
    except RemoteNode.DoesNotExist:
        raise Exception(f"Node '{node_name}' is not active or does not exist.")

    url = f"{node.url}{endpoint}"
    auth = aiohttp.BasicAuth(node.username, node.password)

    async with aiohttp.ClientSession(auth=auth) as session:
        try:
            if method.upper() == 'GET':
                async with session.get(url, timeout=10) as response:
                    response.raise_for_status()
                    return await response.json()
            elif method.upper() == 'POST':
                async with session.post(url, json=data, timeout=10) as response:
                    response.raise_for_status()
                    return await response.json()
            elif method.upper() == 'PUT':
                async with session.put(url, json=data, timeout=10) as response:
                    response.raise_for_status()
                    return await response.json()
            elif method.upper() == 'DELETE':
                async with session.delete(url, timeout=10) as response:
                    response.raise_for_status()
                    return await response.json()
            else:
                raise Exception(f"Unsupported HTTP method: {method}")
        except aiohttp.ClientError as e:
            raise Exception(f"HTTP request to node '{node_name}' failed: {str(e)}")

# async def post_request_to_node(host, url, method='POST', data=None):
#     '''
#     Send an asynchronous HTTP request to a remote node.

#     Parameters:
#         host: The base URL of the remote node.
#         url: The full URL to send the request to.
#         method: {GET, POST, PUT, DELETE}
#         data: data for POST or PUT requests
#     '''
#     # Close any existing database connections to prevent errors in async context
#     connections.close_all()

#     try:
#         node = await sync_to_async(RemoteNode.objects.filter(url=host, is_active=True).first)()
#         if not node:
#             raise RemoteNode.DoesNotExist
#     except RemoteNode.DoesNotExist:
#         raise Exception(f"Node '{host}' is not active or does not exist.")

#     auth = aiohttp.BasicAuth(node.username, node.password)

#     async with aiohttp.ClientSession(auth=auth) as session:
#         try:
#             if method.upper() == 'GET':
#                 async with session.get(url, timeout=10) as response:
#                     response.raise_for_status()
#                     return await response.json()
#             elif method.upper() == 'POST':
#                 async with session.post(url, json=data, timeout=10) as response:
#                     response.raise_for_status()
#                     return await response.json()
#             elif method.upper() == 'PUT':
#                 async with session.put(url, json=data, timeout=10) as response:
#                     response.raise_for_status()
#                     return await response.json()
#             elif method.upper() == 'DELETE':
#                 async with session.delete(url, timeout=10) as response:
#                     response.raise_for_status()
#                     return await response.json()
#             else:
#                 raise Exception(f"Unsupported HTTP method: {method}")
#         except aiohttp.ClientError as e:
#             raise Exception(f"HTTP request to node at '{url}' failed: {str(e)}")
