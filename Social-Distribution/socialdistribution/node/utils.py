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
from uuid import UUID
from django.shortcuts import get_object_or_404
from django.http import Http404
from aiohttp import BasicAuth
from django.db.models import Q
from .models import Author, Post, Comment, Repost, PostLike, CommentLike

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
    if not node:
        print("Couldn't find remote node with host ", host)

    try:
        auth = HTTPBasicAuth(node.username, node.password)
        print("Auth: ", auth)
    except AttributeError:
        print("Couldn't find username and password for remote node with host ", host)
        return None

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

async def post_request_to_node_async(host, url, method='POST', data=None):
    """
    Send an asynchronous HTTP request to a remote node without waiting for a response.

    Parameters:
        host (str): The host of the remote node.
        url (str): The endpoint to send the request to.
        method (str): {POST, PUT}
        data (dict): Data for POST or PUT requests.

    Returns:
        None
    """
    # Fetch the remote node
    node = RemoteNode.objects.filter(Q(url=host) & Q(is_active=True)).first()
    if not node:
        print(f"Couldn't find remote node with host {host}")
        return

    try:
        auth = BasicAuth(node.username, node.password)
    except AttributeError:
        print(f"Couldn't find username and password for remote node with host {host}")
        return

    # Fire-and-forget asynchronous HTTP request
    async with aiohttp.ClientSession(auth=auth) as session:
        try:
            if method.upper() in ['POST', 'PUT']:
                await session.request(method, url, json=data)  # Don't wait for response
            else:
                print(f"Unsupported HTTP method for fire-and-forget: {method}")
        except aiohttp.ClientError as e:
            print(f"Error occurred while sending {method} request to {url}: {e}")


def get_model_instance_by_id(model, id_value):
    """
    Retrieve a model instance by UUID or int ID.
    :param model: The model class to query.
    :param id_value: The ID value (UUID or int).
    :return: The model instance if found.
    :raises Http404: If no matching instance is found.
    """
    try:
        # If id_value is already a UUID object, use it directly
        if isinstance(id_value, UUID):
            return get_object_or_404(model, id=id_value)
        
        # Attempt to parse id_value as a UUID string
        uuid_id = UUID(str(id_value), version=4)
        return get_object_or_404(model, id=uuid_id)
    except (ValueError, TypeError):
        try:
            # Fallback to int ID
            int_id = int(id_value)
            return get_object_or_404(model, id=int_id)
        except (ValueError, TypeError):
            raise Http404(f"{model.__name__} with the provided ID does not exist.")
        
def get_author_by_id(id_value):
    return get_model_instance_by_id(Author, id_value)

def get_post_by_id(id_value):
    return get_model_instance_by_id(Post, id_value)

def get_comment_by_id(id_value):
    return get_model_instance_by_id(Comment, id_value)

def get_repost_by_id(id_value):
    return get_model_instance_by_id(Repost, id_value)

def get_post_like_by_id(id_value):
    return get_model_instance_by_id(PostLike, id_value)

def get_comment_like_by_id(id_value):
    return get_model_instance_by_id(CommentLike, id_value)

def get_post_by_id_and_author(post_id, author_id):
    """
    Retrieve a Post instance by UUID or int for both `post_id` and `author_id`.
    :param post_id: The ID of the Post (UUID or int).
    :param author_id: The ID of the Author (UUID or int).
    :return: The Post instance if found.
    :raises Http404: If no matching instance is found.
    """
    # Parse post_id
    try:
        post_uuid = post_id if isinstance(post_id, UUID) else UUID(str(post_id), version=4)
    except (ValueError, TypeError):
        try:
            post_uuid = int(post_id)
        except (ValueError, TypeError):
            raise Http404("Invalid post_id provided.")

    # Parse author_id
    try:
        author_uuid = author_id if isinstance(author_id, UUID) else UUID(str(author_id), version=4)
    except (ValueError, TypeError):
        try:
            author_uuid = int(author_id)
        except (ValueError, TypeError):
            raise Http404("Invalid author_id provided.")

    # Fetch the post with the parsed IDs
    return get_object_or_404(Post, pk=post_uuid, author_id=author_uuid)


def get_like_instance(model, like_id, liker_id):
    """
    Retrieve an instance of a like model (PostLike or CommentLike) 
    by object_id and liker__id, supporting both UUID and integer keys.

    Args:
        model (models.Model): The model to query (PostLike or CommentLike).
        like_id (str): The object_id to filter by, as UUID or int.
        liker_id (str): The liker__id to filter by, as UUID or int.

    Returns:
        models.Model: An instance of the specified model.

    Raises:
        Http404: If the object does not exist.
    """
    # Parse like_id
    try:
        like_uuid = like_id if isinstance(like_id, UUID) else UUID(str(like_id), version=4)
    except (ValueError, TypeError):
        try:
            like_uuid = int(like_id)
        except (ValueError, TypeError):
            raise Http404("Invalid like_id provided.")

    # Parse liker_id
    try:
        liker_uuid = liker_id if isinstance(liker_id, UUID) else UUID(str(liker_id), version=4)
    except (ValueError, TypeError):
        try:
            liker_uuid = int(liker_id)
        except (ValueError, TypeError):
            raise Http404("Invalid liker_id provided.")

    # Fetch the like instance with the parsed IDs
    return get_object_or_404(model, object_id=like_uuid, liker__id=liker_uuid)