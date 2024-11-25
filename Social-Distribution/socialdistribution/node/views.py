from crypt import methods
import uuid
import datetime
from django.shortcuts import render
from django.http import JsonResponse
import django
from django.core import signing
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
import asyncio
from asgiref.sync import sync_to_async
from django.db import connections
from urllib.parse import urlparse
from .utils import get_author_by_id, get_post_by_id, get_comment_by_id, get_repost_by_id, get_post_like_by_id, get_comment_like_by_id, get_post_by_id_and_author, get_like_instance
from django.views.generic import ListView
from rest_framework.views import APIView

# from node.serializers import serializer

from .models import Post, Author, PostLike, Comment, Like, Follow, Repost, CommentLike, RemoteNode
from django.contrib import messages
from django.db.models import Q, Count, Exists, OuterRef, Subquery
from .serializers import AuthorProfileSerializer, PostSerializer, PostLikeSerializer, PostLikesSerializer, AuthorSerializer, \
    CommentsSerializer, CommentSerializer, CommentLikeSerializer, CommentLikesSerializer
import datetime
import requests
import os
from .forms import AuthorProfileForm
from django.core.paginator import Paginator
from .forms import ImageUploadForm
import http.client
import json
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.decorators import login_required
from .utils import get_authenticated_user_id, AuthenticationFailed, send_request_to_node, post_request_to_node
from rest_framework.response import Response
from rest_framework import status
from urllib.parse import unquote
from rest_framework.parsers import JSONParser
import base64


#NODES = RemoteNode.objects.filter(is_active=True).values_list('name', flat=True)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_authors_list(request):
    page = request.GET.get('page')  # Number of pages to include
    size = request.GET.get('size')  # Number of records per page\
    query = request.GET.get('q', '')  # Search query

    # Filter authors based on the query if it exists
    if query:
        authors = Author.objects.filter(
            Q(display_name__icontains=query)
        )
    else:
        authors = Author.objects.all()

    # Use Paginator to split the queryset into pages
    if page is not None and size is not None:
        page = int(page)  # Convert page to an integer
        size = int(size)  # Convert size to an integer
        paginator = Paginator(authors, size)

        # Ensure the requested page doesn't exceed total number of pages
        if page > paginator.num_pages:
            page = paginator.num_pages

        # Collect all authors up to the requested page
        author_list = []
        current_page = paginator.page(page)
        author_list.extend([{
            "type": "author",
            "id": f"{author.url}",
            "host": author.host,
            "displayName": author.display_name,
            "github": "https://github.com/" + author.github,
            "profileImage": author.profile_image.url if author.profile_image else '',
            "page": author.page
        } for author in current_page if '@foreignnode.com' not in author.email])
    else:
        author_list = [{
            "type": "author",
            "id": f"{author.url}",
            "host": author.host,
            "displayName": author.display_name,
            "github": "https://github.com/" + author.github,
            "profileImage": author.profile_image.url if author.profile_image else '',
            "page": author.page
        } for author in authors if '@foreignnode.com' not in author.email]

    response_data = {
        "type": "authors",
        "authors": author_list,
    }

    return JsonResponse(response_data, status=200)

# @api_view(['GET'])
# def authors_list(request):
#     print("Host: ", request.get_host())
#     query = request.GET.get('q', None)
#     page = request.GET.get('page', None)
#     size = request.GET.get('size', None)

#     # Construct the URL for the API endpoint
#     api_url = request.build_absolute_uri(reverse('api_authors_list'))
#     if (page and size) or query:
#         api_url = api_url[:-1]

#     if page and size:
#         api_url += f'?page={page}&size={size}'

#     if query:
#         api_url += f'&q={query}'


#     user = get_author(request)
#     access_token = AccessToken.for_user(user)
#     headers = {
#         'Authorization': f'Bearer {access_token}'
#     }
    
#     # Make the GET request to the API endpoint
#     responses = []
#     response = requests.get(api_url, headers=headers, cookies=request.COOKIES)
#     responses.append(response)
#     for node in NODES:
#         if page and size:

#             response = send_request_to_node(node, f'api/authors?page={page}&size={size}')
#             print("Response: ", response)
#         else:
#             response = send_request_to_node(node, f'api/authors/')
#             print("Response: ", response)
#         responses.append(response)
#     # print("Response: ", response)
#     # print("Response text: ", response.text)
#     # print("Response body: ", response.json())
#     print("Responses: ", responses)
#     authors = []
#     for response in responses:
#         authors += response.json().get('authors', []) if response.status_code == 200 else []

#     for author in authors:
#         if not Author.objects.filter(url=author['id']).exists():
#             Author.objects.update_or_create(
#                 url=author['id'],
#                 defaults={
#                     'url': author['id'],
#                     'host': author['host'],
#                     'display_name': author['displayName'],
#                     'github': author['github'],
#                     'page': author['page'],
#                     'profile_image': author['profileImage'],
#                 }
#             )

#         author_from_db = Author.objects.filter(url=author['id']).first()

#         print(author['id'])
#         # author['id_num']= int((author['id'].split('https://darkgoldenrod/api/authors/')[0])[0])
#         author['linkable'] = author['id'].startswith(f"https://{request.get_host()}/api/authors/")
#         print(author['id'])
#         print(author['id'].split(f'https://{request.get_host()}/api/authors/'))
#         author['id_num'] = author_from_db.id
#         print(author['id_num'])
#         # find authors logged-in user is already following
#         author['is_following'] = Follow.objects.filter(follower=f"https://{request.get_host()}/api/authors/"+str(user.id)).exists()
#         # print(author['is_following'])

#     context = {
#         'authors': authors,
#         'query': query,
#         'total_pages': response.json().get('total_pages', 1) if response.status_code == 200 else 1,
#     }

#     return render(request, 'authors.html', context)


@api_view(['GET'])
def authors_list(request):
    print("Host: ", request.get_host())
    
    query = request.GET.get('q', None)
    page = request.GET.get('page', None)
    size = request.GET.get('size', None)
    user = get_author(request)

    # Get local authors directly
    local_authors = Author.objects.all()
    if query:
        local_authors = local_authors.filter(display_name__icontains=query)

    if page and size:
        paginator = Paginator(local_authors, size)
        local_authors = paginator.get_page(page)
    else:
        local_authors = local_authors[:50]  # Limit to 50 authors

    authors = [{
        "type": "author",
        "id": f"{author.url}",
        "host": author.host,
        "displayName": author.display_name,
        "github": author.github,
        "profileImage": author.profile_image.url if author.profile_image else '',
        "page": author.page
    } for author in local_authors]
    
    NODES = list(RemoteNode.objects.filter(is_active=True).values_list('name', flat=True))

    # Fetch authors from external nodes asynchronously
    async def fetch_authors():
        tasks = []
        for node_name in NODES:
            if page and size:
                endpoint = f'api/authors?page={page}&size={size}'
            else:
                endpoint = 'api/authors/'
            tasks.append(send_request_to_node(node_name, endpoint))
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        node_authors = []
        for response in responses:
            if isinstance(response, Exception):
                # Handle exceptions
                print(f"Error fetching from node: {response}")
                continue
            if response and 'authors' in response:
                node_authors.extend(response['authors'])
        print("Node authors: ", node_authors)
        return node_authors

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    external_authors = loop.run_until_complete(fetch_authors())

    authors.extend(external_authors)

    # Update or create authors in bulk
    author_urls = [author['id'] for author in authors]
    existing_authors = set(Author.objects.filter(url__in=author_urls).values_list('url', flat=True))
    authors_to_create = []
    for author in authors:
        if author['id'] not in existing_authors:
            print(author)
            try:
                authors_to_create.append(Author(
                    url=author['id'],
                    host=author['host'],
                    display_name=author['displayName'],
                    github=author['github'],
                    page=author['page'],
                    profile_image=author['profileImage'],
                    email=f"{author['id']}@foreignnode.com",
                ))
            except Exception as e:
                print("Author has issue with: ", e)
                authors.remove(author)
    Author.objects.bulk_create(authors_to_create)

    # Update author data with additional info
    for author in authors:
        author['linkable'] = author['id'].startswith(f"https://{request.get_host()}/api/authors/")
        author_from_db = Author.objects.filter(url=author['id']).first()
        author['id_num'] = author_from_db.id if author_from_db else None
        author['is_following'] = Follow.objects.filter(
            follower=f"https://{request.get_host()}/api/authors/{user.id}",
            following=author['id'],
            approved=True
        ).exists()

    context = {
        'authors': authors,
        'query': query,
        'total_pages': 1,  # Adjust as needed
    }

    return render(request, 'authors.html', context)



def editor(request):
    """
    Open menu to edit contents for a post request
    """
    return render(request, "editor.html")

@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated])
def edit_post(request, post_id):
    author = get_author(request)
    #post = get_object_or_404(Post, id=post_id)
    post = get_post_by_id(post_id)

    if author is None:
        return HttpResponseForbidden("You must be logged in to edit posts.")

    if post.author != author:
        return HttpResponseForbidden("You are not allowed to edit this post.")

    if request.method == 'POST':

        title = request.POST.get('title')
        description = request.POST.get('description')
        contentType = request.POST.get('contentType')
        visibility = request.POST.get('visibility')

        if not title or not description:
            messages.error(request, "Title and description cannot be empty.")
            return render(request, 'edit_post.html', {
                'post': post,
                'author_id': author.id,
            })

        post.title = title
        post.description = description
        post.visibility = visibility
        post.published = timezone.now()

        if contentType == 'plain':
            content = request.POST.get('plain-content')
            if not content:
                messages.error(request, "Content cannot be empty for Plaintext.")
                return render(request, 'edit_post.html', {'post': post})
            post.contentType = 'text/plain'
            post.text_content = content
            post.image_content = None  # Remove image if switching from image to text

        elif contentType == 'markdown':
            content = request.POST.get('markdown-content')
            if not content:
                messages.error(request, "Content cannot be empty for Markdown.")
                return render(request, 'edit_post.html', {'post': post})
            post.contentType = 'text/markdown'
            post.text_content = content
            post.image_content = None  # Remove image if switching from image to text

        elif contentType == 'image':
            image = request.FILES.get('image-content')
            if image:
                file_suffix = os.path.splitext(image.name)[1][1:]  # Get file extension without dot
                post.contentType = f'image/{file_suffix.lower()}'
                post.image_content = image
                post.text_content = None  # Remove text if switching from text to image
            else:
                # If no new image is uploaded, keep the existing image_content
                if not post.image_content:
                    messages.error(request, "No image uploaded and no existing image to retain.")
                    return render(request, 'edit_post.html', {'post': post})
                # Else, keep the existing image and contentType
        else:
            messages.error(request, "Invalid content type.")
            return render(request, 'edit_post.html', {'post': post})

        post.save()
        
        print("contentType:", contentType)
        print("plain_content:", request.POST.get('plain_content'))
        print("markdown_content:", request.POST.get('markdown_content'))
        print("image_content:", request.FILES.get('image_content'))

        print(f"Searching for followers following: https://{request.get_host()}/api/authors/{post.author.id}")
        followers = Follow.objects.filter(following=f"https://{request.get_host()}/api/authors/{post.author.id}")
        print("Sending to the following followers: " + str(followers))

        # for follower in followers:
        #     json_content = PostSerializer(post).data
        #     print("sending POST to: " + follower.follower)
        #     post_request_to_node(follower.follower, follower.follower +'/inbox', 'POST', json_content)

        for follower in followers:
            json_content = PostSerializer(post).data
            follower_url = follower.follower
            print("sending POST to: " + follower_url)

            # Extract base URL from follower's URL
            parsed_url = urlparse(follower_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"

            # Send the POST request to the follower's inbox
            inbox_url = follower_url.rstrip('/') + '/inbox'

            print("base_url: ", base_url)
            print("inbox_url: ", inbox_url)
            print("json_content: ", json_content)
            # Now call post_request_to_node with base_url
            post_request_to_node(base_url, inbox_url, 'POST', json_content)

        return redirect('view_post', post_id=post.id)

    else:
        return render(request, 'edit_post.html', {
            'post': post,
            'author_id': author.id,
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_post(request, author_id):
    author = get_author(request)
    contentType = request.POST["contentType"]
    print(request.POST)
    if contentType not in ['text/plain', 'text/markdown', 'image/png', 'image/jpeg']:
        # Check whether content is from AJAX or an external API call
        # For AJAX formatting:
        if contentType != "image":
            contentType = 'text/' + contentType
            content = request.POST.getlist("content")
            if contentType == 'text/plain':
                content = content[0]
            else:
                content = content[1]
            post = Post(title=request.POST["title"],
                        description=request.POST["description"],
                        text_content=content,
                        contentType=contentType,
                        visibility=request.POST["visibility"],
                        published=timezone.make_aware(datetime.datetime.now(), datetime.timezone.utc),
                        author=author,
                        )
            post.save()
        else:
            image = request.FILES["content"]
            file_suffix = os.path.splitext(image.name)[1]
            contentType = request.POST["contentType"]
            contentType += '/' + file_suffix[1:]
            post = Post(title=request.POST["title"],
                        description=request.POST["description"],
                        image_content=image,
                        contentType=contentType,
                        visibility=request.POST["visibility"],
                        published=timezone.make_aware(datetime.datetime.now(), datetime.timezone.utc),
                        author=author,
                        )
            post.save()
    else:   # Post creation for API spec
        if 'image' in contentType:
            post = Post(title=request.POST["title"],
                        description=request.POST["description"],
                        image_content=request.POST["image"],
                        contentType=contentType,
                        visibility=request.POST["visibility"],
                        published=timezone.make_aware(datetime.datetime.now(), datetime.timezone.utc),
                        author=author,
                        )
            post.save()
        else:
            post = Post(title=request.POST["title"],
                        description=request.POST["description"],
                        text_content=request.POST["content"],
                        contentType=contentType,
                        visibility=request.POST["visibility"],
                        published=timezone.make_aware(datetime.datetime.now(), datetime.timezone.utc),
                        author=author,
                        )
            post.save()
            
    post_url = f"https://{request.get_host()}/api/authors/{author.id}/posts/{post.id}"
    post.url = post_url
    post.save()  
    
    print(f"Searching for followers following: https://{request.get_host()}/api/authors/{author_id}")
    followers = Follow.objects.filter(following=f"https://{request.get_host()}/api/authors/{author_id}")
    print("Sending to the following followers: " + str(followers))
    
    # for follower in followers:
    #     json_content = PostSerializer(post).data
    #     print("sending POST to: " + follower.follower)
    #     post_request_to_node(follower.follower, follower.follower +'/inbox', 'POST', json_content)
        
    for follower in followers:
        json_content = PostSerializer(post).data
        follower_url = follower.follower
        print("sending POST to: " + follower_url)

        # Extract base URL from follower's URL
        parsed_url = urlparse(follower_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"

        # Send the POST request to the follower's inbox
        inbox_url = follower_url.rstrip('/') + '/inbox'

        print("base_url: ", base_url)
        print("inbox_url: ", inbox_url)
        print("json_content: ", json_content)
        # Now call post_request_to_node with base_url
        post_request_to_node(base_url, inbox_url, 'POST', json_content)
    return JsonResponse({"message": "Post created successfully", "url": reverse(view_post, args=[post.id])}, status=303)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def author_posts(request, author_id):
    """
    Create a new post or return author's posts.
    """
    if request.method == 'POST':
        author = get_author(request)
        contentType = request.POST["contentType"]
        print(request.POST)
        if contentType not in ['text/plain', 'text/markdown', 'image/png', 'image/jpeg']:
            # Check whether content is from AJAX or an external API call
            # For AJAX formatting:
            if contentType != "image":
                contentType = 'text/' + contentType
                content = request.POST.getlist("content")
                if contentType == 'text/plain':
                    content = content[0]
                else:
                    content = content[1]
                post = Post(title=request.POST["title"],
                            description=request.POST["description"],
                            text_content=content,
                            contentType=contentType,
                            visibility=request.POST["visibility"],
                            published=timezone.make_aware(datetime.datetime.now(), datetime.timezone.utc),
                            author=author,
                            )
                post.save()
            else:
                image = request.FILES["content"]
                file_suffix = os.path.splitext(image.name)[1]
                contentType = request.POST["contentType"]
                contentType += '/' + file_suffix[1:]
                post = Post(title=request.POST["title"],
                            description=request.POST["description"],
                            image_content=image,
                            contentType=contentType,
                            visibility=request.POST["visibility"],
                            published=timezone.make_aware(datetime.datetime.now(), datetime.timezone.utc),
                            author=author,
                            )
                post.save()
        else:   # Post creation for API spec
            if 'image' in contentType:
                post = Post(title=request.POST["title"],
                            description=request.POST["description"],
                            image_content=request.POST["image"],
                            contentType=contentType,
                            visibility=request.POST["visibility"],
                            published=timezone.make_aware(datetime.datetime.now(), datetime.timezone.utc),
                            author=author,
                            )
                post.save()
            else:
                post = Post(title=request.POST["title"],
                            description=request.POST["description"],
                            text_content=request.POST["content"],
                            contentType=contentType,
                            visibility=request.POST["visibility"],
                            published=timezone.make_aware(datetime.datetime.now(), datetime.timezone.utc),
                            author=author,
                            )
                post.save()
        print(f"Searching for followers following: https://{request.get_host()}/api/authors/{author_id}")
        followers = Follow.objects.filter(following=f"https://{request.get_host()}/api/authors/{author_id}")
        print("Sending to the following followers: " + str(followers))
        
        # for follower in followers:
        #     json_content = PostSerializer(post).data
        #     print("sending POST to: " + follower.follower)
        #     post_request_to_node(follower.follower, follower.follower +'/inbox', 'POST', json_content)
            
        for follower in followers:
            json_content = PostSerializer(post).data
            follower_url = follower.follower
            print("sending POST to: " + follower_url)

            # Extract base URL from follower's URL
            parsed_url = urlparse(follower_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"

            # Send the POST request to the follower's inbox
            inbox_url = follower_url.rstrip('/') + '/inbox'

            print("base_url: ", base_url)
            print("inbox_url: ", inbox_url)
            print("json_content: ", json_content)
            # Now call post_request_to_node with base_url
            post_request_to_node(base_url, inbox_url, 'POST', json_content)
        return JsonResponse({"message": "Post created successfully", "url": reverse(view_post, args=[post.id])}, status=303)
    elif request.method == 'GET':
        return get_posts_from_author(request, author_id)

    return JsonResponse({"error": "Invalid request method"}, status=400)


def get_posts_from_author(request, author_id):
    requester = get_author(request)
    #author = get_object_or_404(Author, id=author_id)
    author = get_author_by_id(author_id)
    
    if requester == author:
        posts = Post.objects.filter(author=author)
    else:
        posts = Post.objects.filter(author=author, visibility = 'PUBLIC')

    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data)

def delete_post(request, post_id):
    author = get_author(request)
    #post = get_object_or_404(Post, id=post_id)
    post = get_post_by_id(post_id)

    # if post.author != author:
    #     return HttpResponseForbidden(f"You are not allowed to delete this post. Author: {post.author} but user: {author}")

    if request.method == 'POST':
        # Set the visibility to 'DELETED'
        post.visibility = 'DELETED'
        post.save()
        messages.success(request, "Post has been deleted.")
        return redirect('index')

# @api_view(['GET', 'POST'])
# @permission_classes([IsAuthenticated])
# def local_api_like(request, id):
#     #liked_post = get_object_or_404(Post, id=id)
#     liked_post = get_post_by_id(id)
#     comment_author = liked_post.author
#     current_author = get_author(request)

#     post_owner = liked_post.author
#     print(current_author)
#     print(post_owner)

#     like_id = f"{current_author.url}/liked/{PostLike.objects.count()+1}"
#     object_id = f"{post_author.url}/posts/{liked_post.id}"
#     like_request = {
#         "type" : "like",
#         "author" : {
#             "type" : "author",
#             "id": current_author.url,
#             "host": current_author.host,
#             "displayName": current_author.display_name,
#             "github": current_author.github,
#             "profileImage": current_author.profile_image.url if current_author.profile_image else None,
#             "page": current_author.url,
#         },
#         "published" : datetime.datetime.now().isoformat(),
#         "id" : like_id,
#         "object" : object_id
#     }

#     inbox_url = post_author.url + '/inbox'
#     # access_token = AccessToken.for_user(current_author)

#     try:
#         node = post_author.host[:-4].replace('http://', 'https://')
#         print(f"Node: {node}")
#         print(f"Sent to inbox: {inbox_url}")
#         print(f"Like request: {like_request}")

#         if current_author.host.replace('http://', 'https://') != (node+"api/"):
#             response = post_request_to_node(node, inbox_url, data=like_request)
#             if response and response.status_code in [200, 201]:
#                 return JsonResponse({"message": "Like sent successfully"}, status=201)
#             return JsonResponse({"error": "Failed to send like"}, status=400)
#         else:
#             PostLike.objects.create(liker=current_author, owner=liked_post)

#         return(redirect(f'/node/posts/{id}/'))
#     except Exception as e:
#         print(f"Failed to send post like request: {str(e)}")
#         messages.error(request, "Failed to send post like request. Please try again.")


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def local_api_like(request, id):
    # Get the liked post
    liked_post = get_post_by_id(id)
    post_author = liked_post.author
    current_author = get_author(request)

    # Generate a unique UUID for the like object ID
    like_uuid = uuid.uuid4()
    like_id = f"{current_author.url}/liked/{like_uuid}"

    # Create the like request payload
    like_request = {
        "type": "like",
        "author": {
            "type": "author",
            "id": current_author.url,
            "page": current_author.url,
            "host": current_author.host,
            "displayName": current_author.display_name,
            "github": current_author.github or "",
            "profileImage": current_author.profile_image.url if current_author.profile_image else None,
        },
        "published": datetime.datetime.now().isoformat(),
        "id": like_id,
        "object": liked_post.url,
    }

    # Inbox URL for the post author
    inbox_url = f"{post_author.url}/inbox"

    try:
        # Determine the node for the post's author
        node = post_author.host.rstrip('/').replace('http://', 'https://')
        node = node[:-3]
        # Log debug information
        print(f"Node: {node}")
        print(f"Sent to inbox: {inbox_url}")
        print(f"Like request: {like_request}")

        # Handle remote and local likes
        if current_author.host.rstrip('/') != node.rstrip('/'):
            # Send the like request to a remote node's inbox
            response = post_request_to_node(node, inbox_url, data=like_request)
            if response and response.status_code in [200, 201]:
                return redirect(f'/node/posts/{id}/')
            return JsonResponse({"error": "Failed to send like"}, status=400)
        else:
            # Save the like locally using the `Like` model
            like = PostLike.objects.create(
                object_id=like_uuid,
                liker=current_author,
                created_at=django.utils.timezone.now(),
            )
            like.save()

        # Redirect to the post after liking
        return redirect(f'/node/posts/{id}/')
    except Exception as e:
        # Handle exceptions and log errors
        print(f"Failed to send post like request: {str(e)}")
        messages.error(request, "Failed to send post like request. Please try again.")
        return JsonResponse({"error": "An error occurred while processing the like"}, status=500)
    
    

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def local_api_like_comment(request, id):
    #liked_comment = get_object_or_404(Comment, id=id)
    liked_comment = get_comment_by_id(id)
    comment_author = liked_comment.author
    current_author = get_author(request)
    print(current_author)

    like_uuid = uuid.uuid4()
    like_id = f"{current_author.url}/liked/{like_uuid}"
    object_id = f"{comment_author.url}/commented/{liked_comment.id}"
    print(object_id)
    like_request = {
        "type" : "like",
        "author" : {
            "type" : "author",
            "id": current_author.url,
            "host": current_author.host,
            "displayName": current_author.display_name,
            "github": current_author.github,
            "profileImage": current_author.profile_image.url if current_author.profile_image else None,
            "page": current_author.url,
        },
        "published" : datetime.datetime.now().isoformat(),
        "id" : like_id,
        "object" : object_id
    }

    inbox_url = f"{comment_author.url}/inbox"
    access_token = AccessToken.for_user(current_author)

    try:
        node = comment_author.host.rstrip('/').replace('http://', 'https://')
        node = node[:-3]
        if current_author.host.rstrip('/') != node.rstrip('/'):
            response = post_request_to_node(node, inbox_url, data=like_request)
            if response and response.status_code in [200, 201]:
                return redirect(f'/node/posts/{id}/')
        else:
            like = CommentLike.objects.create(liker=current_author, owner=liked_comment)
            like.save()

        return(redirect(f'/node/posts/{id}/'))
    except Exception as e:
        print(f"Failed to send comment like request: {str(e)}")
        messages.error(request, "Failed to send comment like request. Please try again.")
        return JsonResponse({"error": "An error occurred while processing the like"}, status=500)
   


def post_like(request, author_id):
    body = json.loads(request.body)

    #post = get_object_or_404(Post, id=body['object'].split('/')[-1])
    post = get_post_by_id(body['object'].split('/')[-1])
    #liker = get_author_by_id(body['id'].split('/')[-3])
    liker = get_object_or_404(Author, url=body["author"]["id"])
    # liker = get_object_or_404(id=author_id)
    like_exists = PostLike.objects.filter(liker=liker, owner=post)

    if not like_exists:
        print('Creating post like object')
        post_like = PostLike.objects.create(liker=liker, owner=post)
        # serializer = PostLikeSerializer(post_like, data=body)
        # if serializer.is_valid():
        #     serializer.save()
        #     return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse({'message' : 'PostLike request processed and created.'}, status=200)
    else:
        return JsonResponse({'message' : 'PostLike already exists, unliking.'}, status=400)
        

def comment_like(request, author_id):
    body = json.loads(request.body)
    #post = get_object_or_404(Post, id=body['object'].split('/')[-1])
    comment = get_comment_by_id(body['object'].split('/')[-1])
    liker = get_author_by_id(body['id'].split('/')[-3])

    comment_like_exists = PostLike.objects.filter(liker=liker, owner=comment)
    

    if not comment_like_exists:
        print('creating comment like object')
        comment_like = CommentLike.objects.create(liker=liker, owner=comment)
        return JsonResponse({'message': 'comment like request processed and created'}, status=200)
    else:
        return JsonResponse({'message': 'comment like already exists, unlike instead'}, status=400)

    # serializer = CommentLikeSerializer(comment_like, data=body)
    # if serializer.is_valid():
    #     serializer.save()
    #     return JsonResponse(serializer.data, statis=status.HTTP_201_CREATED)
    # return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_post_likes(request, author_id, post_id):
    #post = get_object_or_404(Post, pk=post_id, author_id=author_id)
    
    author_id = author_id.split('/')[-1]
    post_id = post_id.split('/')[-1]
    post = get_post_by_id_and_author(post_id, author_id)
    author = get_author_by_id(author_id)
    
    
    page_number = int(request.GET.get('page', 1))
    size = int(request.GET.get('size', 50))
    
    likes = PostLike.objects.filter(owner=post).order_by('-published')
    
    paginator = Paginator(likes, size)
    
    if page_number > paginator.num_pages:
        page_number = paginator.num_pages
        
    current_page = paginator.page(page_number)
    
    response_data = {
        "type": "likes",
        "id": f"https://{author.host}authors/{post.author.id}/posts/{post_id}/likes",
        "page": f"https://{author.host}authors/{post.author.id}/posts/{post_id}",
        "page_number": page_number,
        "size": size,
        "count": likes.count(),
        "src": [PostLikeSerializer(like).data for like in current_page]
    }
    
    return Response(response_data)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_post_likes_by_id(request, post_url):
    post_id = post_url.split('/')[-1]
    author_id = post_url.split('/authors/')[-1].split('/')[0]
    
    #post = get_object_or_404(Post, pk=post_id, author_id=author_id)
    post = get_post_by_id_and_author(post_id, author_id)
    #author = get_object_or_404(Author, pk=author_id)
    author = get_author_by_id(author_id)
    
    page_number = int(request.GET.get('page', 1))
    size = int(request.GET.get('size', 50))
    
    likes = PostLike.objects.filter(owner=post).order_by('-created_at')
    
    paginator = Paginator(likes, size)
    
    if page_number > paginator.num_pages:
        page_number = paginator.num_pages
        
    current_page = paginator.page(page_number)
    
    response_data = {
        "type": "likes",
        "id": f"{author.host}authors/{post.author.id}/posts/{post_id}/likes",
        "page": f"{author.host}authors/{post.author.id}/posts/{post_id}",
        "page_number": page_number,
        "size": size,
        "count": likes.count(),
        "src": [PostLikeSerializer(like).data for like in current_page]
    }
    
    return Response(response_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_comment_likes(request, author_id, post_id, comment_fqid):

    comment_id = comment_fqid.split('/')[-1]
    comment_id = unquote(comment_id)

    comment = get_comment_by_id(comment_id)

    try:
        author = get_author_by_id(author_id)
    except (ValueError, Author.DoesNotExist) as e:
        author = None
        print(f"Comments not found: ")

    # if not author:
    #     author = Author.objects.filter()

    page_number = int(request.GET.get('page', 1))
    size = int(request.GET.get('size', 50))
    
    likes = CommentLike.objects.filter(owner=comment).order_by('-published')
    
    paginator = Paginator(likes, size)
    
    if page_number > paginator.num_pages:
        page_number = paginator.num_pages
    
    current_page = paginator.page(page_number)
    
    response_data = {
        "type": "likes",
        "id": f"{author.host()}/authors/{author_id}/comments/{comment_id}/likes",
        "page": f"{author.host()}/authors/{author_id}/comments/{comment_id}",
        "page_number": page_number,
        "size": size,
        "count": likes.count(),
        "src": [CommentLikeSerializer(like).data for like in current_page]
    }
    
    return Response(response_data)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def likes_by_author(request, author_id):
    #author = get_object_or_404(Author, id=author_id)
    author = get_author_by_id(author_id)

    post_likes = PostLike.objects.filter(liker=author)
    comment_likes = CommentLike.objects.filter(liker=author)
    all_likes = list(post_likes) + list(comment_likes)

    page_number = request.GET.get('page', 1)
    size = request.GET.get('size', 50)

    if page_number is not None and size is not None:
        page_number = int(page_number)
        size = int(size)
        paginator = Paginator(all_likes, size)
        
        if page > paginator.num_pages:
            page = paginator.num_pages
            
        current_page = paginator.page(page)
        
        likes_list = []
        for like in current_page:
            if isinstance(like, PostLike):
                likes_list.append(PostLikeSerializer(like).data)
            else:  # CommentLike
                likes_list.append(CommentLikeSerializer(like).data)
    else:
        likes_list = []
        for like in all_likes:
            if isinstance(like, PostLike):
                likes_list.append(PostLikeSerializer(like).data)
            else:  # CommentLike
                likes_list.append(CommentLikeSerializer(like).data)
    
    response_data = {
        "type": "likes",
        "page": f"{author.host}/authors/{author_id}/liked",
        "id": f"{author.host}/authors/{author_id}/liked",
        "page_number": int(page) if page else 1,
        "size": int(size) if size else len(all_likes),
        "count": len(all_likes),
        "src": likes_list
    }
    return JsonResponse(response_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_like(request, author_id, like_id):
    """
    GET: Retrieve a single like by its ID
    URL: ://service/api/authors/{AUTHOR_ID}/liked/{LIKE_ID}
    """
    try:
        if PostLike.objects.filter(object_id=like_id, liker__id=author_id).exists():
            #like = get_object_or_404(PostLike, object_id=like_id, liker__id=author_id)
            like = get_like_instance(PostLike, like_id, author_id)
            serializer = PostLikeSerializer(like)
            return Response(serializer.data)
        
        elif CommentLike.objects.filter(object_id=like_id, liker__id=author_id).exists():
            #like = get_object_or_404(CommentLike, object_id=like_id, liker__id=author_id)
            like = get_like_instance(CommentLike, like_id, author_id)
            serializer = CommentLikeSerializer(like)
            return Response(serializer.data)
        else:
            return Response({"error": "Like not found"}, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_author_likes_by_id(request, author_fqid):
    author_id = author_fqid.split('/')[-1]
    #author = get_object_or_404(Author, id=author_id)
    author = get_author_by_id(author_id)

    post_likes = PostLike.objects.filter(liker=author)
    comment_likes = CommentLike.objects.filter(liker=author)
    all_likes = list(post_likes) + list(comment_likes)
    
    page_number = int(request.GET.get('page', 1))
    size = int(request.GET.get('size', 50))
    
    paginator = Paginator(all_likes, size)
    
    if page_number > paginator.num_pages:
        page_number = paginator.num_pages
            
    current_page = paginator.page(page_number)
    
    likes_list = []
    for like in current_page:
        if isinstance(like, PostLike):
            likes_list.append(PostLikeSerializer(like).data)
        else: 
            likes_list.append(CommentLikeSerializer(like).data)
    
    response_data = {
        "type": "likes",
        "page": f"https://{author.host}authors/{author_id}/liked",
        "id": f"https://{author.host}authors/{author_id}/liked",
        "page_number": page_number,
        "size": size,
        "count": len(all_likes),
        "src": likes_list
    }
    
    return JsonResponse(response_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_like_by_id(request, like_fqid):
    like_id = unquote(like_fqid)
    like_id = like_id.rstrip('/').split('/')

    try:
        # split_like = like_fqid.split('/')
        id = like_id[-1]
        author_id = like_id[-2] 
        
        like = None
        #author = get_object_or_404(Author, id=author_id)
        author = get_author_by_id(author_id)
        
        if PostLike.objects.filter(object_id=id, liker=author).exists():
            #like = get_object_or_404(PostLike, object_id=id, liker=author)
            like = get_like_instance(PostLike, id, author)
            serializer = PostLikeSerializer(like)
        elif CommentLike.objects.filter(object_id=id, liker=author).exists():
            #like = get_object_or_404(CommentLike, object_id=id, liker=author)
            like = get_like_instance(CommentLike, id, author)
            serializer = CommentLikeSerializer(like)
        else:
            return Response({"error": "Like not found"}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.data)
        
    except (IndexError, ValueError):
        return Response({"error": "Invalid like ID format"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@parser_classes([JSONParser])
def post_comments(request, author_id, post_id):
    """
    GET: Retrieve comments on a post
    POST: Add a comment to a post
    """
    try:
        author = Author.objects.get(id=author_id)
        post = Post.objects.get(id=post_id)
    except (Author.DoesNotExist, Post.DoesNotExist):
        return JsonResponse({'error': 'Author or Post not found'}, status=404)

    if request.method == 'GET':
        comments = Comment.objects.filter(post=post).order_by('-published')
        serializer = CommentSerializer(comments, many=True)
        response_data = {
            "type": "comments",
            "page": request.build_absolute_uri(),
            "id": f"{post.author.url}/posts/{post.id}/comments",
            "page_number": 1,
            "size": len(comments),
            "count": len(comments),
            "src": serializer.data,
        }
        return Response(response_data)

    elif request.method == 'POST':
        # Add a comment to the post
        data = request.data

        if data.get('type') != 'comment':
            return JsonResponse({'error': 'Invalid type, expected "comment".'}, status=400)

        authenticated_author = get_author(request)
        if authenticated_author is None:
            return HttpResponseForbidden("You must be logged in to post a comment.")

        comment = Comment(
            post=post,
            author=authenticated_author,
            text=data.get('comment', ''),
            published=timezone.now(),
        )
        comment.save()

        # Serialize the comment
        comment_data = CommentSerializer(comment).data

        # Forward the comment to the post's author inbox if the post is from a remote author
        if post.author.host != f'https://{request.get_host()}/api/':
            inbox_url = f"{post.author.url}/inbox"
            try:
                print("Sending comment to: ", inbox_url)
                print("Host: ", post.author.host)
                post_request_to_node(post.author.host, inbox_url, 'POST', comment_data)
            except Exception as e:
                print(f"Failed to send comment to inbox: {str(e)}")

        return Response(comment_data, status=201)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_comment(request, id):
    """
    Add a comment to a question
    Get question from ID, fill out model details with request,
    save model, go to results page
    """
    if request.method != "POST":
        return HttpResponse(status=400)
    #post = get_object_or_404(Post, pk=id)
    post = get_post_by_id(id)

    # Get request contents
    author = get_author(request)
    text = request.POST["content"]

    if not author:
        return HttpResponseForbidden("You must be logged in to post a comment.")

    new_comment = Comment(post=post, text=text, author=author)
    new_comment.save()
    
    # Generate comment URL
    comment_url = f"https://{request.get_host()}/api/authors/{author.id}/commented/{new_comment.id}"

    # Construct the response payload
    comment_data = {
        "type": "comment",
        "author": {
            "type": "author",
            "id": author.url,
            "host": author.host,
            "displayName": author.display_name,
            "github": author.github,
            "profileImage": author.profile_image.url if author.profile_image else None,
            "page": author.url,
        },
        "comment": new_comment.text,
        "contentType": "text/plain",
        "published": new_comment.published.isoformat(),
        "id": comment_url,
        "post": post.url,
        "likes": {
            "type": "likes",
            "page": f"https://{request.get_host()}/api/authors/{post.author.id}/posts/{post.id}/comments/{new_comment.id}",
            "id": f"https://{request.get_host()}/api/authors/{post.author.id}/posts/{post.id}/comments/{new_comment.id}/likes",
            "page_number": 1,
            "size": 50,
            "count": 0,
            "src": [],
        },
    }

    if request.method == 'POST':
        # Serialize the comment
        #comment_data = CommentSerializer(new_comment).data

        # Forward the comment to the post's author inbox if the post is from a remote author
        if post.author.host != f'https://{request.get_host()}/api/':
            inbox_url = f"{post.author.url}/inbox"
            try:
                print("Sending comment to: ", inbox_url)
                print("Host: ", post.author.host[:-4])
                print("Comment data: ", comment_data)
                post_request_to_node(post.author.host[:-4], inbox_url, 'POST', comment_data)
            except Exception as e:
                print(f"Failed to send comment to inbox: {str(e)}")
                
    return(redirect(f'/node/posts/{id}/'))

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def add_comment(request, id):
#     """
#     Add a comment to a post, with a response matching the specified format.
#     """
#     if request.method != "POST":
#         return HttpResponse(status=400)

#     # Retrieve the post
#     post = get_post_by_id(id)
#     if not post:
#         return JsonResponse({"error": "Post not found."}, status=404)

#     # Get the authenticated author
#     author = get_author(request)
#     if not author:
#         return HttpResponseForbidden("You must be logged in to post a comment.")

#     # Get the comment text and content type
#     text = request.data.get("comment", "")
#     content_type = request.data.get("contentType", "text/plain")
#     if not text:
#         return JsonResponse({"error": "Comment content cannot be empty."}, status=400)

#     # Create the comment
#     new_comment = Comment(
#         post=post,
#         text=text,
#         author=author,
#         content_type=content_type,
#         published=timezone.now(),
#     )
#     new_comment.save()

#     # Generate comment URL
#     comment_url = f"https://{request.get_host()}/api/authors/{author.id}/commented/{new_comment.id}"

#     # Construct the response payload
#     comment_data = {
#         "type": "comment",
#         "author": {
#             "type": "author",
#             "id": author.url,
#             "host": author.host,
#             "displayName": author.display_name,
#             "github": author.github,
#             "profileImage": author.profile_image.url if author.profile_image else None,
#             "page": author.url,
#         },
#         "comment": new_comment.text,
#         "contentType": new_comment.content_type,
#         "published": new_comment.published.isoformat(),
#         "id": comment_url,
#         "post": f"https://{request.get_host()}/api/authors/{post.author.id}/posts/{post.id}",
#         "likes": {
#             "type": "likes",
#             "page": f"https://{request.get_host()}/api/authors/{post.author.id}/posts/{post.id}/comments/{new_comment.id}",
#             "id": f"https://{request.get_host()}/api/authors/{post.author.id}/posts/{post.id}/comments/{new_comment.id}/likes",
#             "page_number": 1,
#             "size": 50,
#             "count": 0,
#             "src": [],
#         },
#     }

#     # Forward the comment to the post's author's inbox if they are on a remote node
#     if post.author.host != f'https://{request.get_host()}/api/':
#         inbox_url = f"{post.author.url}/inbox"
#         try:
#             print("Sending comment to:", inbox_url)
#             post_request_to_node(post.author.host.rstrip('/'), inbox_url, 'POST', comment_data)
#         except Exception as e:
#             print(f"Failed to send comment to inbox: {str(e)}")

#     return JsonResponse(comment_data, status=201)


        # inbox_url = f"{post.author.url}/inbox"
        # try:
        #     print("Sending comment to: ", inbox_url)
        #     print("Host: ", post.author.host)
        #     post_request_to_node(post.author.host, inbox_url, 'POST', comment_data)
        # except Exception as e:
        #     print(f"Failed to send comment to inbox: {str(e)}")

        #return Response(comment_data, status=201)

    # json_content = CommentSerializer(new_comment).data

    # # Iterate through each follower
    # for follower in followers:
    #     try:
    #         # Extract the follower's URL and prepare the inbox URL
    #         url = follower.follower.url  # Assuming `follower.follower.url` is the follower's URL
    #         print("Sending POST to: " + url)

    #         # Extract base URL from the follower's URL
    #         parsed_url = urlparse(url)
    #         base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"

    #         # Construct the follower's inbox URL
    #         inbox_url = url.rstrip('/') + '/inbox'

    #         print("base_url: ", base_url)
    #         print("inbox_url: ", inbox_url)
    #         print("json_content: ", json_content)

    #         # Send the POST request to the follower's inbox
    #         post_request_to_node(base_url, inbox_url, 'POST', json_content)
    #     except Exception as e:
    #         print(f"Failed to send comment to {url}: {e}")
            
            
            
            
    
    
    # followers = Follow.objects.filter(following=f"{post.author.host}authors/{post.author.id}")
    # print("Sending comment to people following: ", f"{post.author.host}authors/{post.author.id}")
    # print("Sending comment to: ", followers)
    # try:
    #     json_content = CommentSerializer(new_comment).data
    #     url = post.author.url
    #     print("sending POST to: " + url)

    #     # Extract base URL from follower's URL
    #     parsed_url = urlparse(url)
    #     base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"

    #     # Send the POST request to the follower's inbox
    #     inbox_url = url.rstrip('/') + '/inbox'

    #     print("base_url: ", base_url)
    #     print("inbox_url: ", inbox_url)
    #     print("json_content: ", json_content)
    #     # Now call post_request_to_node with base_url
    #     post_request_to_node(base_url, inbox_url, 'POST', json_content)
    # except Exception as e:
    #     print(e)
    # # Return to question
    #return(redirect(f'/node/posts/{id}/'))

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def author_commented(request, author_id):
    """
    Handles GET and POST requests for `://service/api/authors/{AUTHOR_SERIAL}/commented`
    """
    try:
        author = Author.objects.get(id=author_id)
    except Author.DoesNotExist:
        return JsonResponse({"error": "Author not found"}, status=404)

    if request.method == 'GET':
        # Get the list of comments made by the author
        comments = Comment.objects.filter(author=author).order_by('-published')

        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = request.GET.get('size', 10)
        result_page = paginator.paginate_queryset(comments, request)

        serializer = CommentSerializer(result_page, many=True)
        response_data = {
            "type": "comments",
            "page": request.build_absolute_uri(),
            "id": f"{author.url}/commented",
            "page_number": paginator.page.number,
            "size": paginator.page_size,
            "count": paginator.page.paginator.count,
            "src": serializer.data,
        }
        return Response(response_data)

    elif request.method == 'POST':
        # Ensure the authenticated user is the author
        if request.user != author:
            return HttpResponseForbidden("You are not allowed to post comments as this author.")

        data = request.data

        if data.get('type') != 'comment':
            return JsonResponse({'error': 'Invalid type, expected "comment".'}, status=400)

        # Get post ID from data['post']
        post_url = data.get('post', '')
        if not post_url:
            return JsonResponse({'error': 'Post URL is required.'}, status=400)

        post_id = post_url.rstrip('/').split('/')[-1]
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return JsonResponse({'error': 'Post not found.'}, status=404)

        # Create the comment
        comment = Comment(
            post=post,
            author=author,
            text=data.get('comment', ''),
            published=timezone.now(),
        )
        comment.save()

        # Serialize the comment
        comment_data = CommentSerializer(comment).data

        # Forward the comment to the post's author inbox
        inbox_url = f"{post.author.url}/inbox"
        try:
            post_request_to_node(post.author.host.rstrip('/'), inbox_url, 'POST', comment_data)
        except Exception as e:
            print(f"Failed to send comment to inbox: {str(e)}")

        return Response(comment_data, status=201)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_comment_by_fqid(request, comment_fqid):
    """
    GET [local] get this comment by its Fully Qualified ID (FQID)
    URL: `://service/api/commented/{COMMENT_FQID}`
    """
    # Decode the FQID
    decoded_comment_fqid = unquote(comment_fqid)
    comment_id = decoded_comment_fqid.rstrip('/').split('/')[-1]

    try:
        comment = Comment.objects.get(id=comment_id)
    except Comment.DoesNotExist:
        return JsonResponse({"error": "Comment not found"}, status=404)

    serializer = CommentSerializer(comment)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_post(request, post_id):
    """
    For viewing a post
    Returns 403 for visibility conflicts
    Otherwise, render the post
    """

    #post = get_object_or_404(Post, id=post_id)
    post = get_post_by_id(post_id)
    author = get_author(request)
    liked = False

    if post.author != author: # if user that is not the creator is attempting to view
        if post.visibility == "FRIENDS":
            try:
                follow = get_object_or_404(Follow, follower=author, following = post.author)
            except:
                return HttpResponse(status=403)
            if follow.is_friend():
                return HttpResponse(status=403)

    if post.visibility == "PRIVATE":
        if post.author != author:
            return HttpResponse(status=403)

    if PostLike.objects.filter(owner=post, liker=author).exists():
        liked = True

    # user_likes strategy obtained from Microsoft Copilot, Oct. 2024
    # Find likes from current user matching the queried comment
    user_likes = CommentLike.objects.filter(owner=OuterRef('pk'), liker=author)

    return render(request, "post.html", {
        "post": post,
        "id": post_id,
        'likes': PostLike.objects.filter(owner=post),
        'author': author,
        'liked' : liked,
        'author_id': author.id,
        'comments': Comment.objects.filter(post=post)
                  .annotate(likes=Count('commentlike'),
                            liked=Exists(user_likes)
                            ),
    })

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def profile(request, author_id):
#     '''
#     Render the contents of profile of desired author
#     including author's posts, author's GitHub activity, and author's profile details
#     :param request:
#     :param author_id: id of author whose profile is currently being viewed
#     :return: html rendition of profile.html with the appropriate content
#     '''
#     viewing_author = get_object_or_404(Author, id=author_id)
#     current_author = get_author(request) # logged in author
#     ownProfile = (viewing_author == current_author)

#     access_token = AccessToken.for_user(current_author)
#     headers = {
#         'Authorization': f'Bearer {access_token}'
#     }
#     api_url = request.build_absolute_uri(reverse('single_author', kwargs={'author_id': viewing_author.id}))
#     response = requests.get(api_url, headers=headers, cookies=request.COOKIES)
#     author_data = response.json()

#     user = {
#             'id': author_data['id'],
#             'host': author_data['host'],
#             'display_name': author_data['displayName'],
#             'github': author_data['github'],
#             'page': author_data['page'],
#             'profile_image': author_data['profileImage'],
#             'description':author_data['description'],
#         }

#     is_following = Follow.objects.filter( # if logged in author following the user
#         follower=f"https://{request.get_host()}/api/authors/" + str(current_author.id),
#         following=f"https://{request.get_host()}/api/authors/" + str(author_id),
#         approved=True,
#     ).exists()
#     if is_following:
#         is_followback = Follow.objects.filter(  # ... see if user is following back
#             follower=f"https://{request.get_host()}/api/authors/" + str(author_id),
#             following=f"https://{request.get_host()}/api/authors/" + str(current_author.id),
#             approved=True,
#         ).exists()
#         is_pending = False
#     else:
#         is_followback = False
#         is_pending = Follow.objects.filter( # if logged in author following the user
#             follower=f"https://{request.get_host()}/api/authors/" + str(current_author.id),
#             following=f"https://{request.get_host()}/api/authors/" + str(author_id),
#             approved=False,
#         ).exists()

#     visible_tags = ['PUBLIC']
#     if is_followback or user==current_author: # if logged in user is friends with user or if logged in user viewing own profile
#         visible_tags.append('FRIENDS') # show friend visibility posts
#         if user==current_author: # if logged in user viewing own profile, show unlisted posts too
#             visible_tags.append('UNLISTED')

#     authors_posts = Post.objects.filter(author=viewing_author, visibility__in= visible_tags).exclude(description="Public Github Activity").order_by('-published') # most recent on top
#     retrieve_github(viewing_author)
#     github_posts = Post.objects.filter(author=viewing_author, visibility__in=visible_tags, description="Public Github Activity").order_by('-published')

#     # Followers: people who follow the user
#     followers_count = Follow.objects.filter(
#         following=f"https://{request.get_host()}/api/authors/{author_id}",
#         approved=True
#     ).count()

#     # Following: people the user follows
#     # This returns a list of users that `author_id` is following
#     followed_users = Follow.objects.filter(
#         follower=f"https://{request.get_host()}/api/authors/{author_id}",
#         approved=True).values_list('following', flat=True)
#     following_count = followed_users.count()
#     print(followed_users)

#     author_url = f"https://{request.get_host()}/api/authors/{author_id}"

#     # Friends: mutual follows
#     friends_count = Follow.objects.filter(
#         follower__in=followed_users,  # Users that are followed by `author_id`
#         following=author_url,  # `author_id` is the `following`
#         approved=True
#     ).count()  # Count mutual follow relationships


#     return render(request, "profile/profile.html", {
#         'user': user,
#         'posts': authors_posts,
#         'ownProfile': ownProfile,
#         'is_following': is_following,
#         'is_pending': is_pending,
#         'activity': github_posts,
#         'followers_count': followers_count,
#         'following_count': following_count,
#         'friends_count': friends_count,
#     })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request, author_id):
    '''
    Render the contents of the profile of the desired author,
    including the author's posts, GitHub activity, and profile details.
    '''
    #viewing_author = get_object_or_404(Author, id=author_id)
    viewing_author = get_author_by_id(author_id)
    current_author = get_author(request)  # Logged-in author
    own_profile = (viewing_author == current_author)

    # Build the user data directly from the `viewing_author` object
    user = {
        'id': viewing_author.id,
        'host': viewing_author.host,
        'display_name': viewing_author.display_name,
        'github': viewing_author.github,
        'page': viewing_author.page,
        'profile_image': viewing_author.profile_image.url if viewing_author.profile_image else '',
        'description': viewing_author.description,
    }

    # Determine if the current user is following the viewing author
    is_following = Follow.objects.filter(
        follower=f"https://{request.get_host()}/api/authors/{current_author.id}",
        following=viewing_author.url,
        approved=True,
    ).exists()

    # Check if there is a pending follow request
    is_pending = False
    if not is_following:
        is_pending = Follow.objects.filter(
            follower=f"https://{request.get_host()}/api/authors/{current_author.id}",
            following=viewing_author.url,
            approved=False,
        ).exists()

    # Determine if the viewing author is following back
    is_followback = Follow.objects.filter(
        follower=viewing_author.url,
        following=f"https://{request.get_host()}/api/authors/{current_author.id}",
        approved=True,
    ).exists()

    # Determine visible posts based on relationship
    visible_tags = ['PUBLIC']
    if is_followback or own_profile:
        visible_tags.append('FRIENDS')
        if own_profile:
            visible_tags.append('UNLISTED')

    # Retrieve posts
    authors_posts = Post.objects.filter(
        author=viewing_author,
        visibility__in=visible_tags
    ).exclude(description="Public Github Activity").order_by('-published')

    # Retrieve GitHub activity
    retrieve_github(viewing_author)
    github_posts = Post.objects.filter(
        author=viewing_author,
        visibility__in=visible_tags,
        description="Public Github Activity"
    ).order_by('-published')

    # Followers count
    followers_count = Follow.objects.filter(
        following=viewing_author.url,
        approved=True
    ).count()

    # Following count
    following_count = Follow.objects.filter(
        follower=viewing_author.url,
        approved=True
    ).count()

    # Friends count (mutual follows)
    friends_count = Follow.objects.filter(
        follower__in=Follow.objects.filter(
            follower=viewing_author.url,
            approved=True
        ).values_list('following', flat=True),
        following=viewing_author.url,
        approved=True
    ).count()

    return render(request, "profile/profile.html", {
        'user': user,
        'posts': authors_posts,
        'ownProfile': own_profile,
        'is_following': is_following,
        'is_pending': is_pending,
        'activity': github_posts,
        'followers_count': followers_count,
        'following_count': following_count,
        'friends_count': friends_count,
    })

def retrieve_github(user):
    '''
    Retrieve GitHub public activity of author and create Post objects if there is any
    Makes use of the api.github.com
    :param user: Author object
    :return: None
    '''
    # 10/19/2024
    # Me: How to retrieve public github activity of a user, based on their username, to display in an html
    # OpenAI ChatGPT 40 mini generated:
    # Starts here
    conn = http.client.HTTPSConnection("api.github.com")
    headers = {
        'User-Agent': 'node'
    }
    conn.request("GET", f"/users/{user.github}/events/public", headers=headers)
    res = conn.getresponse()
    data = res.read()
    activity = json.loads(data.decode("utf-8")) if res.status == 200 else []
    # Ends here


    followers = Follow.objects.filter(following=user.url, approved = True)
    print(followers)


    # 10/28/2024
    # Me: Retrieve the different event types, the repo, the date in each event in the json and create them into post if they do not yet exist in the database
    # OpenAI ChatGPT 40 mini generated:
    # Starts here
    for event in activity:
        # Extract the event type and creation date
        event_type = event.get("type")
        created_at = event.get("created_at")

        # Create a better description based on the event type
        if event_type == "PushEvent":
            post_description = f"Pushed {len(event.get('payload', {}).get('commits', []))} commit(s) to {event['repo']['name']}."
        elif event_type == "ForkEvent":
            post_description = f"Forked the repository {event['repo']['name']}."
        elif event_type == "CreateEvent":
            post_description = f"Created a new {event['payload'].get('ref_type')} '{event['payload'].get('ref')}' in {event['repo']['name']}."
        elif event_type == "PullRequestEvent":
            post_description = f"Opened a pull request '{event['payload']['pull_request']['title']}' in {event['repo']['name']}."
        elif event_type == "IssuesEvent":
            post_description = f"Created an issue '{event['payload']['issue']['title']}' in {event['repo']['name']}."
        else:
            post_description = f"Performed a {event_type.lower()} action in {event['repo']['name']}."

        # Convert created_at string to a datetime object
        naive_published_date = datetime.datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
        published_date = timezone.make_aware(naive_published_date, datetime.timezone.utc)

        # Check for existing post and create new post if it doesn't exist
        if not Post.objects.filter(author=user, title=event_type, text_content=post_description,
                                   published=published_date).exists():
            post = Post.objects.create(
                author=user,
                title=event_type,
                description="Public Github Activity",
                visibility='PUBLIC',
                published=published_date,  # Set the published date from the activity
                text_content=post_description,
            )
    # Ends here

            #  then send the new github activity post to all followers
            for follower in followers:
                json_content = PostSerializer(post).data
                follower_url = follower.follower
                print("sending POST to: " + follower_url)


                # Extract base URL from follower's URL
                parsed_url = urlparse(follower_url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"

                # Send the POST request to the follower's inbox
                inbox_url = follower_url.rstrip('/') + '/inbox'

                print("base_url: ", base_url)
                print("inbox_url: ", inbox_url)
                print("json_content: ", json_content)
                # Now call post_request_to_node with base_url
                post_request_to_node(base_url, inbox_url, 'POST', json_content)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def api_single_author_fqid(request, author_fqid):
    author_id = author_fqid.split('/')[-1]
    # print(author_id)
    # return api_single_author(request, author_id)
    #user = get_object_or_404(Author, id=author_id)
    print("uuid????????")
    print(author_fqid)
    author_id = unquote(author_id)

    # Initialize user to None
    user = None

    # First, try to get by primary key (integer ID)
    try:
        #user = Author.objects.get(pk=int(author_id))
        user = get_author_by_id(author_id)
    except (ValueError, Author.DoesNotExist):
        pass  # Not an integer ID or author with this ID does not exist

    if not user:
        # Try to get by URL equals author_id (in case it's a full URL)
        user = Author.objects.filter(url=author_id).first()

    if not user:
        # Try to get by URL ending with /authors/{author_id}
        user = Author.objects.filter(url__endswith=f"/authors/{author_id}").first()

    if not user:
        # Author not found
        nonexistent_author = {
            "message": "This user does not exist",
        }
        return JsonResponse(nonexistent_author, status=404)


    if request.method == 'GET':
        if user is None:
            nonexistent_author = {
                "message": "This user does not exist",
            }
            return JsonResponse(nonexistent_author, status=404)
        else:
            author_data = {
                "type": "author",
                "id": user.id,
                "host": user.host,
                "displayName": user.display_name,
                "github": "https://github.com/" + user.github if user.github else "",
                "profileImage": user.profile_image.url if user.profile_image else None,
                "page": user.page,
                "description": user.description,
            }
            return JsonResponse(author_data, status=200)

    if request.method == 'PUT':
        print("serializer")
        serializer = AuthorProfileSerializer(user, data=request.data)
        print("giithub")
        original_github = user.github

        if serializer.is_valid():
            if original_github != serializer.validated_data.get('github'):
                Post.objects.filter(author=user, description="Public Github Activity").delete()
                retrieve_github(user)
            print("uuid?")
            print (user.id)
            serializer.save()
            author_data = {
                "type": "author",
                "id": author_fqid,
                "host": user.host,
                "displayName": user.display_name,
                "github": "https://github.com/" + user.github if user.github else "",
                "profileImage": user.profile_image.url if user.profile_image else None,
                "page": user.page,
                "description": user.description,
            }
            return JsonResponse(author_data, status=200)
        else:
            error_data = {
                "message": "Invalid edit made.",
                'errors': serializer.errors,
            }
            return JsonResponse(error_data, status=400)

# @api_view(['GET', 'PUT'])
# @permission_classes([IsAuthenticated])
# def api_single_author(request, author_id):
#     #user = get_object_or_404(Author, id=author_id)
#
#     author_id = unquote(author_id)
#     print(author_id)
#     # Initialize user to None
#     user = None
#
#     # First, try to get by primary key (integer ID)
#     try:
#         #user = Author.objects.get(pk=int(author_id))
#         user = get_author_by_id(author_id)
#     except (ValueError, Author.DoesNotExist):
#         pass  # Not an integer ID or author with this ID does not exist
#
#     if not user:
#         # Try to get by URL equals author_id (in case it's a full URL)
#         user = Author.objects.filter(url=author_id).first()
#
#     if not user:
#         # Try to get by URL ending with /authors/{author_id}
#         user = Author.objects.filter(url__endswith=f"/authors/{author_id}").first()
#
#     if not user:
#         # Author not found
#         nonexistent_author = {
#             "message": "This user does not exist",
#         }
#         return JsonResponse(nonexistent_author, status=404)
#
#
#     if request.method == 'GET':
#         if user is None:
#             nonexistent_author = {
#                 "message": "This user does not exist",
#             }
#             return JsonResponse(nonexistent_author, status=404)
#         else:
#             author_data = {
#                 "type": "author",
#                 "id": user.id,
#                 "host": user.host,
#                 "displayName": user.display_name,
#                 "github": "https://github.com/" + user.github if user.github else "",
#                 "profileImage": user.profile_image.url if user.profile_image else None,
#                 "page": user.page,
#                 "description": user.description,
#             }
#             return JsonResponse(author_data, status=200)
#
#     if request.method == 'PUT':
#         serializer = AuthorProfileSerializer(user, data=request.data)
#
#         original_github = user.github
#
#         if serializer.is_valid():
#             if original_github != serializer.validated_data.get('github'):
#                 Post.objects.filter(author=user, description="Public Github Activity").delete()
#
#             serializer.save()
#             author_data = {
#                 "type": "author",
#                 "id": user.id,
#                 "host": user.host,
#                 "displayName": user.display_name,
#                 "github": "https://github.com/" + user.github if user.github else "",
#                 "profileImage": user.profile_image.url if user.profile_image else None,
#                 "page": user.page,
#                 "description": user.description,
#             }
#             return JsonResponse(author_data, status=200)
#         else:
#             error_data = {
#                 "message": "Invalid edit made.",
#                 'errors': serializer.errors,
#             }
#             return JsonResponse(error_data, status=400)

def edit_profile(request,author_id):
    '''
    Fetch logged in author's profile details and display them in editable inputs
    :param request:
    :param author_id: id of logged in author who is attempting to edit their own profile
    :return: html rendition of edit_profile.html with the appropriate content
    '''
    #user = get_object_or_404(Author, id=author_id)
    user = get_author_by_id(author_id)
    serializer = AuthorProfileSerializer(user)
    return render(request, 'profile/edit_profile.html', {'user': serializer.data})

@api_view(['GET'])
def followers_following_friends(request, author_id):
    '''
    Display list of authors who are either, followers, followings, or friends of user whose profile is currently being viewed
    :param request:
    :param author_id: id of author whose profile is currently being viewed
    :return: html rendition of follower_following.html with the appropriate content
    '''
    #author = get_object_or_404(Author, id=author_id)
    author = get_author_by_id(author_id)
    current_author = get_author(request)
    # check if user viewing the follow is viewing their own followings
    is_own = (author==current_author)

    profileUserUrl = author.url  # user of the profile
    users = []

    see_follower = request.GET.get('see_follower')

    # see friends
    if see_follower is None:
        follow_objects = Follow.objects.filter(follower=profileUserUrl, approved=True)
        friends = [person.following for person in follow_objects if person.is_friend()]
        for friend_url in friends:
            users.append(get_object_or_404(Author, url=friend_url))
        title = "Friends"
    else:
        # see followers
        if see_follower == "true":
            # use the api to get followers

            # access_token = AccessToken.for_user(author)
            # headers = {
            #     'Authorization': f'Bearer {access_token}'
            # }
            #
            # responses = []
            # api_url = request.build_absolute_uri(reverse('list_all_followers', kwargs={'author_id': author_id}))
            # response = requests.get(api_url, headers=headers, cookies=request.COOKIES)
            # print(response.json())
            # responses.append(response)
            #
            # for response in responses:
            #     users += response.json().get('followers', []) if response.status_code == 200 else []

            follow_objects= Follow.objects.filter(following=profileUserUrl, approved=True).values_list('follower', flat=True)
            for url in follow_objects:
                users.append(get_object_or_404(Author, url=url))
            title = "Followers"
        elif see_follower == 'false':
            users = Follow.objects.filter(follower=profileUserUrl, approved=True).values_list('following', flat=True)
            title = "Followings"

    user_authors = Author.objects.filter(url__in=users)

    # serialize
    # author_data = [{'id': author.id, 'display_name': author.display_name} for author in user_authors]

    # if request.accepted_renderer.format == 'json':
    #     author_data = [{'id': author.id, 'display_name': author.display_name} for author in user_authors]
    #     return Response({
    #         'title': title,
    #         'authors': author_data
    #     })

    print("these are the users")
    print(users)
    for user in users:
        print(user.display_name)
    return render(request, 'follower_following.html', {
        'authors': users,
        'DisplayTitle': title,
        'is_own': is_own,
        'current_author_id': str(current_author.id),
    })

def get_author(request):
    """
    Retrieves the authenticated Author instance.
    Returns:
        Author instance if authenticated, else None.
    """
    if request.user.is_authenticated:
        return request.user
    return None

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def local_api_follow(request, author_id):
    # send a Post request to INBOX with the follow request object
    # Called by authors.html
    # get current author id and follow author id for POST request body
    # author_id should have the full url (include node and everything) inside.
    current_author = get_author(request)
    #author_to_follow = get_object_or_404(Author, id=author_id)
    author_to_follow = get_author_by_id(author_id)

    actor_profile_image = current_author.profile_image.url if current_author.profile_image else ""
    followee_profile_image = author_to_follow.profile_image.url if author_to_follow.profile_image else ""
    
    # Construct the follow request object
    follow_request = {
        "type": "follow",
        "summary": f"{current_author.display_name} wants to follow {author_to_follow.display_name}",
        "actor": {
            "type": "author",
            "id": current_author.url,
            "host": current_author.host,
            "displayName": current_author.display_name,
            "github": current_author.github,
            "profileImage": actor_profile_image,
            "page": current_author.url,
        },
        "object": {
            "type": "author",
            "id": author_to_follow.url,
            "host": author_to_follow.host,
            "displayName": author_to_follow.display_name,
            "github": author_to_follow.github,
            "profileImage": followee_profile_image,
            "page": author_to_follow.url,
        }
    }

    # access_token = AccessToken.for_user(current_author)
    # headers = {
    #     'Authorization': f'Bearer {access_token}'
    # }

    # Send the POST request to the target author's inbox endpoint
    # inbox_url = request.build_absolute_uri(reverse('inbox', args=[author_id]))
    inbox_url = author_to_follow.url + "/inbox"
    access_token = AccessToken.for_user(current_author)
    try:
        node = author_to_follow.host[:-4].replace('https://','https://')
        print(f"Node: {node}")
        print(f"Author to follow: {inbox_url}")
        print(f"Follow request: {follow_request}")

        print(current_author.host.replace('https://','https://'))
        print(node+"api/")
        # if remote node
        if current_author.host.replace('https://','https://') != (node+"api/"):
            response = post_request_to_node(node, inbox_url, data=follow_request)
        # else local node
        else:
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            # response = requests.post(inbox_url, json=follow_request, headers=headers, cookies=request.COOKIES)
        # create follow object after successful post

        Follow.objects.create(following=author_to_follow.url, follower=current_author.url, approved=True)

        # if response.status_code in [200, 201]:
        print("Sent Follow request")
        print(f"Sent to: {inbox_url}")
        # print(f"Response URL: {response.url}")
        messages.success(request, "Follow request sent successfully.")
        # else:
        #     print("Failed to send Follow request")
        #     messages.error(request, "Failed to send follow request. Please try again.")

        return redirect('authors')
    except Exception as e:
        print(f"Failed to send follow request: {str(e)}")
        messages.error(request, "Failed to send follow request. Please try again.")

def add_external_comment(request, author_id):
    """
    Adds comment objects from an API according to
    either the 'comment' or 'comments' specification
    """
    body = json.loads(request.body)

    if body['type'] == 'comment':   # Single comment
        post_url = body.get('post', '')
        post_id = post_url.rstrip('/').split('/')[-1]
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return JsonResponse({'error': 'Post not found.'}, status=404)

        # Ensure the author exists or create if necessary
        author_data = body.get('author')
        if not author_data:
            return JsonResponse({'error': 'Author data is required.'}, status=400)

        author_id = author_data.get('id', '').rstrip('/').split('/')[-1]
        author, created = Author.objects.get_or_create(
            url=author_data.get('id'),
            defaults={
                'display_name': author_data.get('displayName', 'Unknown'),
                'host': author_data.get('host', ''),
                'github': author_data.get('github', ''),
                'profile_image': author_data.get('profileImage', ''),
                'email': f"{author_id}@foreignnode.com",
            }
        )

        comment = Comment(
            post=post,
            author=author,
            text=body.get('comment', ''),
            published=body.get('published', timezone.now()),
        )
        comment.save()

        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=201)

    if body['type'] == 'comments':
        for comment in body['src']:
            #new_comment = Comment.objects.create(author_id=author_id, post=get_object_or_404(Post, id=body['post'].split('/')[-1]))
            new_comment = Comment.objects.create(author_id=author_id, post=get_post_by_id(body['post'].split('/')[-1]))
            serializer = CommentSerializer(new_comment, data=comment)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse('Failed to add comment(s)', status=status.HTTP_400_BAD_REQUEST)


def add_external_post(request, author_id):
    """
    Add a post to the database from an inbox call
    """
    body = json.loads(request.body)
    
    author_data = body.get('author', {})
    author_id_from_body = author_data.get('id')
    author = get_object_or_404(Author, url=author_id_from_body)
    #body['author'] = author.id
    
    post_url = body.get('id')
    existing_posts_with_id = Post.objects.filter(url=post_url)
    for post in existing_posts_with_id:
        post.visibility = 'DELETED'
        post.save()
    
    serializer = PostSerializer(data=body)
    if serializer.is_valid():
        serializer.save(author=author, url=post_url)
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    print(serializer.errors)
    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def inbox(request, author_id):
    print("Inbox function ran")
    if request.method == 'POST':
        try:
            print("Inbox POST request received")
            # Parse the request body
            body = json.loads(request.body)
            print("Request body:", body)
            print("Body type:", body['type'])
            if body['type'] == 'follow':
                # Extract relevant information and call follow_author
                follower = body['actor']
                following = body['object']
                print("Follow request type detected")
                return follow_author(follower, following)
            if body['type'] == 'like':
                post_or_comment = body['object']
                if '/posts/' in post_or_comment:
                    return post_like(request, author_id)
                else:   # Comment like
                    return comment_like(request, author_id)
            # Add additional handling for other types (e.g., post, like, comment) as needed
            if body['type'] == 'post':
                return add_external_post(request, author_id)
            if body['type'] == 'comment' or body['type'] == 'comments':
                return add_external_comment(request, author_id)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Failed to parse request body: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'message': 'Method not allowed'}, status=405)


### Is called by def inbox()
# With help from Chat-GPT 4o, OpenAI, 2024-10-14
def follow_author(follower, following):

    print("follow_author ran")

    follower_url = follower['id']
    following_url = following['id']

    print(f'follower: {follower}')
    print(f'following: {following}')

    follow_exists = Follow.objects.filter(follower=follower_url, following=following_url).exists()

    print(f"Tested follow_exists: {follow_exists}")

    if not follow_exists:
        print("Creating follow object")
        Follow.objects.create(follower=follower_url, following=following_url, approved=False)
        
        return JsonResponse({'message': 'Follow request processed successfully'}, status=200)
    else:
        return JsonResponse({'message': 'Follow relationship already exists'}, status=400)

# With help from Chat-GPT 4o, OpenAI, 2024-10-14
@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
def unfollow_author(request, author_id):
    # Get the author being followed
    #author_to_unfollow = get_object_or_404(Author, id=author_id)
    author_to_unfollow = get_author_by_id(author_id)

    # Get the logged-in author (assuming you have a user to author mapping)
    current_author = get_author(request) # Adjust this line to match your user-author mapping

    # Check if the follow relationship already exists
    follow_exists = Follow.objects.filter(follower=current_author.url, following=author_to_unfollow.url).exists()

    if follow_exists:
        # api_url = request.build_absolute_uri(reverse('list_follower'))
        # access_token = AccessToken.for_user(current_author)
        # headers = {
        #     'Authorization': f'Bearer {access_token}'
        # }
        # # Make the GET request to the API endpoint
        # response = requests.delete(api_url, headers=headers, cookies=request.COOKIES)
        #
        # messages.success(request, "You have successfully unfollowed this author.")

        follow = get_object_or_404(Follow, follower=current_author.url, following=author_to_unfollow.url)
        # Delete the Follow object to unfollow the author
        follow.delete()
        messages.success(request, "You have successfully unfollowed this author.")

    if not follow_exists:
        # Create a new follow relationship
        print("No follow relationship exists between these authors.")
        messages.warning(request, "You are not following this author.")

    # Redirect back to the authors list or a success page
    return redirect('authors')

def follow_requests(request, author_id):
    #current_author = get_object_or_404(Author, id=author_id)  # logged in author
    current_author = get_author_by_id(author_id)
    print(current_author.url)
    current_follow_requests = Follow.objects.filter(following=current_author.url, approved=False)
    print(current_follow_requests)
    follower_authors = []
    for a_request in current_follow_requests:
        # follower_id = a_request.follower.replace("https://darkgoldenrod/api/authors/", "")
        follower_author = get_object_or_404(Author, url=a_request.follower)
        follower_authors.append(follower_author)

    return render(request, 'follow_requests.html', {
        'follow_authors': follower_authors,
        'author': current_author,
        'cookies': request.COOKIES,
        'access_token': AccessToken.for_user(current_author),
    })

def approve_follow(request, author_id, follower_id):
    '''
    Approve a submitted follow request, updating it's approved status
    :param request:
    :param author_id: id of author asking to be followed
    :param follower_id: id of author who submitted follow request
    :return: redirection to follow_requests view
    '''
    #follower_author = get_object_or_404(Author, id=follower_id)
    follower_author = get_author_by_id(follower_id)
    #current_author = get_object_or_404(Author, id=author_id)
    current_author = get_author_by_id(author_id)
    follow_request = get_object_or_404(Follow, follower=follower_author.url, following=current_author.url)
    follow_request.approved = True
    follow_request.save()
    return redirect('follow_requests', author_id=author_id)  # Redirect to the profile view after saving

def decline_follow(request, author_id, follower_id):
    '''
    Decline a submitted follow request and delete it from database
    :param request:
    :param author_id: id of author asking to be followed
    :param follower_id: id of author who submitted follow request
    :return: redirection to follow_requests view
    '''
    #follower_author = get_object_or_404(Author, id=follower_id)
    follower_author = get_author_by_id(follower_id)
    #current_author = get_object_or_404(Author, id=author_id)
    current_author = get_author_by_id(author_id)
    follow_request = get_object_or_404(Follow, follower=follower_author.url, following=current_author.url)
    follow_request.delete()
    return redirect('follow_requests', author_id=author_id)  # Redirect to the profile view after saving

# With help from Chat-GPT 4o, OpenAI, 2024-10-14
### WARNING: Only works for posts from authors of the same node right now
# Shows posts from followings and friends
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def display_feed(request):
    """
    Display posts from the authors the logged-in user is following.
    """

    # Get the current user's full author URL
    current_author = get_author(request)

    # Get filter option from URL query parameters (default is 'all')
    filter_option = request.GET.get('filter', 'all')

    # Get the authors that the current user is following
    follow_objects = Follow.objects.filter(follower=current_author.url, approved=True)


    followings = list(follow_objects.values_list('following', flat=True))
    following_authors = Author.objects.filter(url__in=followings)
    cleaned_followings = following_authors.values_list('id', flat=True)

    friends = [follow.following for follow in follow_objects if follow.is_friend()]
    friends_authors = Author.objects.filter(url__in=friends)
    cleaned_friends = friends_authors.values_list('id', flat=True)
    # cleaned_friends = [int(url.replace('https://darkgoldenrod/api/authors/', '')) for url in friends]


    public_posts = Post.objects.filter(visibility__in=['PUBLIC'])

    follow_posts = Post.objects.filter(author__in=cleaned_followings, visibility__in=['PUBLIC', 'UNLISTED'])

    friend_posts = Post.objects.filter(author__in=cleaned_friends, visibility__in=['PUBLIC', 'UNLISTED','FRIENDS'])
    
    reposts = Repost.objects.filter(shared_by__in=cleaned_followings).order_by('-shared_date')

    cleaned_reposts = []
    for repost in reposts:
        post = repost.original_post
        cleaned_reposts.append({
            "id": post.id,
            "title": post.title,
            "description": post.description,
            "author": post.author,
            "published": post.published,
            "text_content": post.text_content,
            "likes": PostLike.objects.filter(owner=post).count(),
            "comments": Comment.objects.filter(post=post).count(),
            "url": reverse("view_post", kwargs={"post_id": post.id}),
            "shared_by": repost.shared_by,
            "shared_date": repost,
            "image_content_url": post.image_content.url if post.image_content and post.image_content.url else None
        })
    
    # print(f"Current Author ID: {current_author}|")  # Debug the current author's ID
    # follower_url = current_author.url
    # print(f"Follower URL: {follower_url}|")  # Debug the full follower URL
    # print(f'Author IDs: {followings}|')
    # print(f"Cleaned Author IDs: {cleaned_followings}|")
    # print(f"Public posts: {public_posts}\n")

    # Retrieve posts from authors the user is following

    # Filter based on the selected option
    if filter_option == "followings":
        posts = (follow_posts | friend_posts).order_by('-published')
    elif filter_option == "public":
        posts = public_posts.order_by('-published')
    elif filter_option == "friends":
        posts = friend_posts.order_by('-published')
    elif filter_option == "reposts":
        cleaned_posts = cleaned_reposts
    else:  # 'all' filter (default)
        posts = (public_posts | follow_posts | friend_posts).distinct().order_by('-published')

    if filter_option != "reposts":
        cleaned_posts = []
        for post in posts:
            cleaned_posts.append({
                "id": post.id,
                "title": post.title,
                "description": post.description,
                "author": post.author,
                "published": post.published,
                "text_content": post.text_content,
                "likes": PostLike.objects.filter(owner=post).count(),
                "comments": Comment.objects.filter(post=post).count(),
                "url": reverse("view_post", kwargs={"post_id": post.id}),
                "image_content_url": post.image_content.url if post.image_content and post.image_content.url else None
            })

    if filter_option == "all":
        cleaned_posts = cleaned_reposts + cleaned_posts



    # likes = [PostLike.objects.filter(owner=post).count() for post in posts]

    # Pagination setup
    paginator = Paginator(cleaned_posts, 10)  # Show 10 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Render the feed template and pass the posts as context
    return render(request, 'feed.html', {'page_obj': page_obj, 'author_id': current_author,})


def repost_post(request, id):
    #post = get_object_or_404(Post, pk=id)
    post = get_post_by_id(id)
    # Only public posts can be shared
    if post.visibility != "PUBLIC":
        return HttpResponseForbidden("Post cannot be shared.")

    shared_post = Repost.objects.create(
        original_post=post,
        shared_by=get_author(request)
    )

    return(redirect(f'/node/posts/{id}/'))

def upload_image(request):
    signed_id = request.COOKIES.get('id')
    id = signing.loads(signed_id)
    #author = get_object_or_404(Author, id=id)
    author = get_author_by_id(id)

    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.author = author
            image.save()
            return redirect('index')
    else:
        form = ImageUploadForm()
    return render(request, 'node_admin/upload_image.html', {'form': form})

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def api_get_post_from_author(request, author_id, post_id):
    if request.method == 'GET':
        return view_post(request, post_id)
    elif request.method == 'PUT':
        return edit_post_api(request, author_id, post_id)
    elif request.method == 'DELETE':
        return delete_post_api(request, author_id, post_id)

def edit_post_api(request, author_id, post_id):
    author = get_author(request)
    #post = get_object_or_404(Post, id=post_id)
    post = get_post_by_id(post_id)
    if post.author != author:
        return HttpResponseForbidden("Post cannot be edited.", status=403)

    data = request.data
    serializer = PostSerializer(post, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
        if author.host == f'https://{request.get_host()}/api/':
            # Distribute posts to connected nodes
            followers = Follow.objects.filter(following=f"{author.host}authors/{author_id})")
            for follower in followers:
                processed_nodes = [f'https://{request.get_host()}/api/']
                if follower.host not in processed_nodes:
                    json_content = PostSerializer(post).data
                    post_request_to_node(follower.host[:-4], follower.url + '/inbox', 'POST', json_content)
                    processed_nodes.append(follower.host)
        return JsonResponse(PostSerializer(post).data)
    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def delete_post_api(request, author_id, post_id):
    author = get_author(request)
    #post = get_object_or_404(Post, id=post_id)
    post = get_post_by_id(post_id)
    if post.author != author:
        return HttpResponseForbidden("Post cannot be deleted.", status=403)

    post.delete()
    return HttpResponse('Post successfully deleted.', status=204)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_post(request, post_id):
    #post = get_object_or_404(Post, pk=post_id)
    post = get_post_by_id(post_id)
    #author = get_object_or_404(Author, id=post.author_id)
    author = get_author_by_id(post.author_id)
    if post.visibility == "FRIENDS":
        follow = get_object_or_404(Follow, follower=author, following=post.author)
        if not follow.is_friend():
            return HttpResponse(403, 'Cannot view this post')
    return JsonResponse(get_serialized_post(post), safe=False)

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def get_comments_from_post(request, post_url):
#     post_id = post_url.split('/')[-1]
#     return get_comments(request, post_id)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_comment(request, author_id, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id, author__id=author_id)
    except Comment.DoesNotExist:
        return JsonResponse({"error": "Comment not found"}, status=404)

    serializer = CommentSerializer(comment)
    return Response(serializer.data)

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def get_comments(request, author_id, post_id):
#     #TO-DO: Pagination/query handling
#     # page_number = request.GET.get('page', 1)
#     # size = request.GET.get('size', 5)
#     #post = get_object_or_404(Post, id=post_id)
#     post = get_post_by_id(post_id)
#     # page = ((page_number - 1) * size)
#     # comments = post.comment_set.all()[page:page + size]
#     serializer = CommentsSerializer(post)
#     return JsonResponse(serializer.data, safe=False)


def get_serialized_post(post):
    return PostSerializer(post).data


# @api_view(['GET', 'PUT', 'DELETE'])
# @permission_classes([IsAuthenticated])
# def followers_view(request, author_id, follower_id=None):
#     author = get_object_or_404(Author, id=author_id)
#     follower_id = request.GET.get('follower_id')  # Get the follower_id from query params
#     follower_host = request.GET.get('follower')  # Get the follower_id from query params
#     print("followers_view ran initial")
#     print("follower_id", follower_id)
#     if request.method == 'GET':
#         if follower_id:
#             print("followers_view ran")
#             # Decode the follower_id URL (assuming it's a URL-encoded ID)
#             decoded_follower_id = unquote(follower_id)
#             # Attempt to find the follower by their URL field, assuming `url_field` holds the unique URL
#             id = decoded_follower_id.split('/')[-1]
#             host = decoded_follower_id.replace(f'authors/{id}', '')
#             print('id in function: ', id)
#             print('host in function: ', host)
#             follower = Author.objects.filter(host=host, id=int(id)).first()
#             if not follower:
#                 return JsonResponse({"error": "Not Found Follower"}, status=404)
#             elif not Follow.objects.filter(following=f"{author.host}authors/{author.id}", follower=f"{follower.host}authors/{follower.id}", approved=True).first():
#                 return JsonResponse({"error": "Not a Follower of Author"}, status=404)

#             # Construct the JSON response manually
#             return JsonResponse({
#                 "type": "author",
#                 "id": follower.id,
#                 "url": follower.url,
#                 "host": follower.host,
#                 "displayName": follower.display_name,
#                 "page": follower.page,
#                 "github": follower.github,
#                 "profileImage": follower.profile_image.url if follower.profile_image else ''
#             })

#         else:
#             # Get all followers and manually construct the response
#             followers_data = []
#             print(author.host)
#             print(author.id)
#             followers = Follow.objects.filter(following=f"{author.host}authors/{author.id}", approved=True)
#             followers = list(followers.values_list('follower', flat=True))
#             print("followers in function", followers)
#             for follower_url in followers:
#                 id = follower_url.split('/')[-1]
#                 host = follower_url.replace(f'authors/{id}', '')
#                 follower = Author.objects.filter(host=host, id=int(id)).first()

#                 followers_data.append({
#                     "type": "author",
#                     "id": follower.id,
#                     "url": follower.url,
#                     "host": follower.host,
#                     "displayName": follower.display_name,
#                     "page": follower.page,
#                     "github": follower.github,
#                     "profileImage": follower.profile_image.url if follower.profile_image else ''
#                 })

#             return JsonResponse({
#                 "type": "followers",
#                 "followers": followers_data
#             })

#     elif request.method == 'PUT':
#         if follower_id:
#             # Decode the follower_id URL (assuming it's a URL-encoded ID)
#             decoded_follower_id = unquote(follower_id)
#             print(follower_id)
#             # print("decoded_follower_id: ", decoded_follower_id)
#             # print("author_url: ", f"{author.host}authors/{author.id}")

#             follow = Follow.objects.get(follower=follower_host + "authors/" + decoded_follower_id,
#                                         following=f"{author.host}authors/{author.id}")

#             follow.approved = True
#             follow.save()
#             return JsonResponse({"status": "follow request approved"}, status=201)
#         else:
#             return JsonResponse({"error": "Missing foreign author ID"}, status=400)

#     elif request.method == 'DELETE':
#         if follower_id:
#             # Decode the follower_id URL (assuming it's a URL-encoded ID)
#             decoded_follower_id = unquote(follower_id)
#             try:
#                 print("decode_follower_id: ", decoded_follower_id)
#                 print("author_url: ", f"{author.host}authors/{author.id}")
#                 follow_instance = Follow.objects.get(follower=decoded_follower_id, following=f"{author.host}authors/{author.id}")
#                 follow_instance.delete()
#                 return JsonResponse({"status": "follow relationship deleted"}, status=204)
#             except Follow.DoesNotExist:
#                 return JsonResponse({"error": "Follow relationship not found"}, status=404)
#         else:
#             return JsonResponse({"error": "Missing foreign author ID"}, status=400)
        
        
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def followers_view(request, author_id, follower_id=None):
    # Since your local authors have integer IDs, convert author_id to integer
    # try:
    #     author_id_int = int(author_id)
    # except ValueError:
    #     return JsonResponse({"error": "Invalid author ID"}, status=400)
    # author = get_object_or_404(Author, id=author_id_int)
    
    author = get_author_by_id(author_id)

    if request.method == 'GET':
        if follower_id:
            # Handle the follower_id as a string (could be UUID or integer)
            follower_url = unquote(follower_id).rstrip('/')
            # Build the follower's URL

            # Check if the follower is in the Follow model
            if not Follow.objects.filter(
                following=author.url,
                follower=follower_url,
                approved=True
            ).exists():
                return JsonResponse({"error": "Not a follower of the author"}, status=404)

            # Try to find the follower in the Author model
            follower = Author.objects.filter(url=follower_url).first()
            if not follower:
                # If the follower is not in the local Author model, you can create a placeholder or return minimal info
                follower_data = {
                    "type": "author",
                    "id": follower_url,
                    "host": decoded_follower_host if follower_host else author.host,
                    "displayName": "",  # You may not have the display name
                    "page": "",
                    "github": "",
                    "profileImage": ""
                }
            else:
                follower_data = {
                    "type": "author",
                    "id": follower_url,
                    "host": follower.host,
                    "displayName": follower.display_name,
                    "page": follower.page,
                    "github": follower.github,
                    "profileImage": follower.profile_image.url if follower.profile_image else ''
                }

            return JsonResponse(follower_data)

        else:
            # Get all followers
            followers = Follow.objects.filter(
                following=author.url,
                approved=True
            ).values_list('follower', flat=True)

            # Fetch all local authors matching the follower URLs in one query
            local_authors = Author.objects.filter(url__in=followers)

            # Create a dictionary for quick lookup
            local_authors_dict = {author.url: author for author in local_authors}

            followers_data = []
            for follower_url in followers:
                if follower_url in local_authors_dict:
                    follower = local_authors_dict[follower_url]
                    follower_data = {
                        "type": "author",
                        "id": follower.url,
                        "host": follower.host,
                        "displayName": follower.display_name,
                        "page": follower.page,
                        "github": follower.github,
                        "profileImage": follower.profile_image.url if follower.profile_image else ''
                    }
                else:
                    # For external authors not in your local Author model
                    # Extract host and id from follower_url
                    follower_id_extracted = follower_url.rstrip('/').split('/')[-1]
                    follower_host_extracted = follower_url.replace(f'authors/{follower_id_extracted}', '')
                    
                    follower_data = {
                        "type": "author",
                        "id": follower_url,
                        "host": follower_host_extracted,
                        "displayName": "",
                        "page": "",
                        "github": "",
                        "profileImage": ""
                    }

                followers_data.append(follower_data)

            return JsonResponse({
                "type": "followers",
                "followers": followers_data
            })

    elif request.method == 'PUT':
        if follower_id:
            # Approve a follow request
            follower_url = unquote(follower_id).rstrip('/')

            try:
                follow = Follow.objects.get(
                    follower=follower_url,
                    following=author.url
                )
                follow.approved = True
                follow.save()
                return JsonResponse({"status": "Follow request approved"}, status=201)
            except Follow.DoesNotExist:
                return JsonResponse({"error": "Follow request not found"}, status=404)
        else:
            return JsonResponse({"error": "Missing follower ID or host"}, status=400)

    elif request.method == 'DELETE':
        if follower_id:
            follower_url = unquote(follower_id).rstrip('/')
            print('DELETE follower_url: ', follower_url)

            try:
                follow_instance = Follow.objects.get(
                    follower=follower_url,
                    following=author.url
                )
                follow_instance.delete()
                return JsonResponse({"status": "Follow relationship deleted"}, status=204)
            except Follow.DoesNotExist:
                return JsonResponse({"error": "Follow relationship not found"}, status=404)
        else:
            return JsonResponse({"error": "Missing follower ID or host"}, status=400)
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_post_image(request, author_id, post_id):
    """
    GET [local, remote] get the public post converted to binary as an image.
    Returns 404 if not an image.
    """
    post = get_post_by_id_and_author(post_id, author_id)
        
    if not post.contentType.endswith(';base64') and post.contentType != 'application/base64':
        return HttpResponse("Not an image post", status=404)
        
    try:
        post_data = PostSerializer(post).data
        decoded_image = base64.b64decode(post.text_content)
        post_data['content'] = decoded_image.decode('utf-8', errors='ignore')
            
        return JsonResponse(post_data)
            
    except Exception as e:
        return HttpResponse("Invalid image data", status=400)    
            
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_post_image_by_id(request, post_fqid):
    """
    GET [local, remote] get the public post converted to binary as an image using FQID.
    Returns 404 if not an image.
    """
    post_id = post_fqid.split('/')[-1]
    post = get_post_by_id(post_id)
        
        # Check if this is an image post
    if not post.contentType.endswith(';base64') and post.contentType != 'application/base64':
        return HttpResponse("Not an image post", status=404)
        
    try:
        post_data = PostSerializer(post).data
        decoded_image = base64.b64decode(post.text_content)
            
        post_data['content'] = decoded_image.decode('utf-8', errors='ignore')
            
        return JsonResponse(post_data)
            
    except Exception as e:
        return HttpResponse("Invalid image data", status=400)