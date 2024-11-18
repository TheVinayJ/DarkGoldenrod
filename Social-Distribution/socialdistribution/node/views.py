from crypt import methods

from django.core import signing
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from django.views.generic import ListView

# from node.serializers import serializer

from .models import Post, Author, PostLike, Comment, Like, Follow, Repost, CommentLike
from django.contrib import messages
from django.db.models import Q, Count, Exists, OuterRef, Subquery
from .serializers import AuthorProfileSerializer, PostSerializer, LikeSerializer, LikesSerializer, AuthorSerializer, \
    CommentsSerializer, CommentSerializer
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
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.decorators import login_required
from .utils import get_authenticated_user_id, AuthenticationFailed, send_request_to_node
from rest_framework.response import Response
from rest_framework import status
from urllib.parse import unquote
from rest_framework.parsers import JSONParser


NODES = ['Duy', 'Aykhan']

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
            "github": author.github,
            "profileImage": author.profile_image.url if author.profile_image else '',
            "page": author.page
        } for author in current_page])
    else:
        author_list = [{
            "type": "author",
            "id": f"{author.url}",
            "host": author.host,
            "displayName": author.display_name,
            "github": author.github,
            "profileImage": author.profile_image.url if author.profile_image else '',
            "page": author.page
        } for author in authors]

    response_data = {
        "type": "authors",
        "authors": author_list,
    }

    return JsonResponse(response_data, status=200)

@api_view(['GET'])
def authors_list(request):
    print("Host: ", request.get_host())
    query = request.GET.get('q', None)
    page = request.GET.get('page', None)
    size = request.GET.get('size', None)

    # Construct the URL for the API endpoint
    api_url = request.build_absolute_uri(reverse('api_authors_list'))
    if (page and size) or query:
        api_url = api_url[:-1]

    if page and size:
        api_url += f'?page={page}&size={size}'

    if query:
        api_url += f'&q={query}'


    user = get_author(request)
    access_token = AccessToken.for_user(user)
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    # Make the GET request to the API endpoint
    responses = []
    response = requests.get(api_url, headers=headers, cookies=request.COOKIES)
    responses.append(response)
    for node in NODES:
        if page and size:

            response = send_request_to_node(node, f'api/authors?page={page}&size={size}')
            print("Response: ", response)
        else:
            response = send_request_to_node(node, f'api/authors/')
            print("Response: ", response)
        responses.append(response)
    # print("Response: ", response)
    # print("Response text: ", response.text)
    # print("Response body: ", response.json())
    print("Responses: ", responses)
    authors = []
    for response in responses:
        authors += response.json().get('authors', []) if response.status_code == 200 else []

    for author in authors:
        Author.objects.update_or_create(
            url=author['id'],
            defaults={
                'url': author['id'],
                'host': author['host'],
                'display_name': author['displayName'],
                'github': author['github'],
                'page': author['page'],
                'profile_image': author['profileImage'],
            }
        )

        author_from_db = Author.objects.filter(url=author['id']).first()

        print(author['id'])
        # author['id_num']= int((author['id'].split('http://darkgoldenrod/api/authors/')[0])[0])
        author['linkable'] = author['id'].startswith(f"http://{request.get_host()}/api/authors/")
        print(author['id'])
        print(author['id'].split(f'http://{request.get_host()}/api/authors/'))
        author['id_num'] = author_from_db.id
        print(author['id_num'])
        # find authors logged-in user is already following
        author['is_following'] = Follow.objects.filter(follower=f"http://{request.get_host()}/api/authors/"+str(user.id)).exists()
        # print(author['is_following'])

    context = {
        'authors': authors,
        'query': query,
        'total_pages': response.json().get('total_pages', 1) if response.status_code == 200 else 1,
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
    post = get_object_or_404(Post, id=post_id)

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

        if author.host == f'http://{request.get_host()}/api/':
            # Distribute posts to connected nodes
            followers = Follow.objects.filter(following=f"{author.host}/authors/{author.id})")
            for follower in followers:
                processed_nodes = [f'http://{request.get_host()}/api/']
                if follower.host not in processed_nodes:
                    json_content = PostSerializer(post).data
                    send_request_to_node(follower.host, follower.id + '/inbox', 'POST', json_content)
                    processed_nodes.append(follower.host)

        return redirect('view_post', post_id=post.id)

    else:
        return render(request, 'edit_post.html', {
            'post': post,
            'author_id': author.id,
        })

@login_required
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
    if author.host == f'http://{request.get_host()}/api/':
        # Distribute posts to connected nodes
        followers = Follow.objects.filter(following=f"{author.host}/authors/{author_id})")
        for follower in followers:
            processed_nodes = [f'http://{request.get_host()}/api/']
            if follower.host not in processed_nodes:
                json_content = PostSerializer(post).data
                send_request_to_node(follower.host, follower.id +'/inbox', 'POST', json_content)
                processed_nodes.append(follower.host)
    return JsonResponse({"message": "Post created successfully", "url": reverse(view_post, args=[post.id])}, status=303)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def author_posts(request, author_id):
    """
    Create a new post or return author's posts.
    """
    if request.method == 'POST':
        return add_post(request, author_id)
    elif request.method == 'GET':
        return get_posts_from_author(request, author_id)

    return JsonResponse({"error": "Invalid request method"}, status=400)


def get_posts_from_author(request, author_id):
    requester = get_author(request)
    author = get_object_or_404(Author, id=author_id)
    if requester == author:
        posts = Post.objects.filter(author=author)
    else:
        posts = Post.objects.filter(author=author, visibility = 'PUBLIC')

    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data)

def delete_post(request, post_id):
    author = get_author(request)
    post = get_object_or_404(Post, id=post_id)

    # if post.author != author:
    #     return HttpResponseForbidden(f"You are not allowed to delete this post. Author: {post.author} but user: {author}")

    if request.method == 'POST':
        # Set the visibility to 'DELETED'
        post.visibility = 'DELETED'
        post.save()
        messages.success(request, "Post has been deleted.")
        return redirect('index')

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def local_api_like(request, id):
    liked_post = get_object_or_404(Post, id=id)
    current_author = get_author(request)

    author_serializer = AuthorSerializer(current_author)
    author_data = author_serializer.data

    like_data = {
        "type": "like",
        "author": author_data,
        "object": f"http://{request.get_host()}/api/authors/{liked_post.author.id}/posts/{liked_post.id}",
        "published": datetime.datetime.now(),
        "id" : f"http://{request.get_host()}/api/authors/{current_author.id}/liked/{PostLike.objects.filter(liker=current_author).count()}"
    }

    print("Like Data: ", like_data)
    
    serializer = LikeSerializer(data=like_data)
    if not serializer.is_valid():
        print("Validation errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    like_object = serializer.data

    inbox_url = request.build_absolute_uri(reverse('inbox', args=[liked_post.author.id]))
    
    try:
        response = requests.post(inbox_url, json=like_object, headers={'Content-Type' : 'application/json'})
        response.raise_for_status()

        return Response({"message": "Like sent to inbox"}, status=status.HTTP_201_CREATED)
    except request.ReqestException as e:
        return Response({"error": f"Failed to send like to inbox: {str(e)}"}, status=status.HTTP_502_BAD_GATEWAY)


def post_like(data):
    """
    Method for liking a post given a post_id
    If already liked by requesting author, unlike
    """
    # author = get_author(request)
    post_url = data['object']
    split_post = post_url.split('/')
    post_id = split_post[-1] # Get last item in list after split
    post = get_object_or_404(Post, pk=post_id)
    liker = data['author']
    liker_id = liker["id"].split('/')[-1]
    author = get_object_or_404(Author, id=liker_id)
    if PostLike.objects.filter(owner=post, liker=author).exists():
        PostLike.objects.filter(owner=post, liker=author).delete()
        return Response({"message": "Post Like removed"}, status=status.HTTP_200_OK)
    else:
        new_like = PostLike(owner=post, liker=author)
        new_like.save()
        return Response({"message": "Post Like created"}, status=status.HTTP_201_CREATED)


def comment_like(data):
    """
    Method for liking a comment given comment ID
    if already liked by requesting author, removes the like
    """
    # author = get_author(request)
    comment_url = data['object']
    comment_id = comment.split('/')
    comment_id = comment_id[-1]
    comment = get_object_or_404(Comment, pk=comment_id)
    
    liker = data['author']
    liker_id = liker["id"].split('/')[-1]
    author = get_object_or_404(Author, id=liker_id)
    if CommentLike.objects.filter(owner=comment, liker=author).exists():
        CommentLike.objects.filter(owner=comment, liker=author).delete()
        return Response({"message": "Comment Like removed"}, status=status.HTTP_200_OK)
    else:
        new_like = CommentLike(owner=comment, liker=author)
        new_like.save()
        return Response({"message": "Comment Like created"}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_post_likes(request, author_id, post_id):
    post = get_object_or_404(Post, id=post_id, author__id=author_id)
    
    page_number = int(request.GET.get('page', 1))
    size = int(request.GET.get('size', 50))
    
    serializer = LikesSerializer(
        post,
        context={
            'page_number': page_number,
            'size': size,
            'request': request
        }
    )
    
    return Response(serializer.data)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_post_likes_by_id(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    return redirect('get_post_likes', 
                   author_id=post.author.id, 
                   post_id=post.id)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_comment_likes(request, author_id, post_id, comment_id):
    """
    GET: Retrieve all likes for a comment
    URL: ://service/api/authors/{AUTHOR_ID}/posts/{POST_ID}/comments/{COMMENT_ID}/likes
    """
    comment = get_object_or_404(Comment, id=comment_id, post__id=post_id, post__author__id=author_id)
    
    page_number = int(request.GET.get('page', 1))
    size = int(request.GET.get('size', 50))
    
    serializer = LikesSerializer(
        comment,  # Pass the comment instance
        context={
            'page_number': page_number,
            'size': size,
            'request': request
        }
    )
    
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_like(request, like_id):
    """
    GET: Retrieve a single like by its FQID
    URL: ://service/api/liked/{LIKE_FQID}
    """
    try:
        split_like = like_id.split('/')
        like_exact_id = split_like[-1] 
        author_id = split_like[1] 
        
        like = None
        author = get_object_or_404(Author, id=author_id)
        
        if PostLike.objects.filter(object_id=like_exact_id, liker=author).exists():
            like = get_object_or_404(PostLike, object_id=like_exact_id, liker=author)
        elif CommentLike.objects.filter(object_id=like_exact_id, liker=author).exists():
            like = get_object_or_404(CommentLike, object_id=like_exact_id, liker=author)
        else:
            return Response({"error": "Like not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = LikeSerializer(like)
        return Response(serializer.data)
        
    except (IndexError, ValueError):
        return Response({"error": "Invalid like ID format"}, status=status.HTTP_400_BAD_REQUEST)

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
    post = get_object_or_404(Post, pk=id)

    # Get request contents
    author = get_author(request)
    text = request.POST["content"]

    if not author:
        return HttpResponseForbidden("You must be logged in to post a comment.")


    new_comment = Comment(post=post, text=text, author=author)
    new_comment.save()
    # Return to question
    return(redirect(f'/node/posts/{id}/'))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_post(request, post_id):
    """
    For viewing a post
    Returns 403 for visibility conflicts
    Otherwise, render the post
    """

    post = get_object_or_404(Post, id=post_id)
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request, author_id):
    '''
    Render the contents of profile of desired author
    including author's posts, author's GitHub activity, and author's profile details
    :param request:
    :param author_id: id of author whose profile is currently being viewed
    :return: html rendition of profile.html with the appropriate content
    '''
    viewing_author = get_object_or_404(Author, id=author_id)
    current_author = get_author(request) # logged in author
    ownProfile = (viewing_author == current_author)

    access_token = AccessToken.for_user(current_author)
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    api_url = request.build_absolute_uri(reverse('single_author', kwargs={'author_id': viewing_author.id}))
    response = requests.get(api_url, headers=headers, cookies=request.COOKIES)
    author_data = response.json()

    user = {
            'id': author_data['id'],
            'host': author_data['host'],
            'display_name': author_data['displayName'],
            'github': author_data['github'],
            'page': author_data['page'],
            'profile_image': author_data['profileImage'],
            'description':author_data['description'],
        }

    is_following = Follow.objects.filter( # if logged in author following the user
        follower=f"http://{request.get_host()}/api/authors/" + str(current_author.id),
        following=f"http://{request.get_host()}/api/authors/" + str(author_id),
        approved=True,
    ).exists()
    if is_following:
        is_followback = Follow.objects.filter(  # ... see if user is following back
            follower=f"http://{request.get_host()}/api/authors/" + str(author_id),
            following=f"http://{request.get_host()}/api/authors/" + str(current_author.id),
            approved=True,
        ).exists()
        is_pending = False
    else:
        is_followback = False
        is_pending = Follow.objects.filter( # if logged in author following the user
            follower=f"http://{request.get_host()}/api/authors/" + str(current_author.id),
            following=f"http://{request.get_host()}/api/authors/" + str(author_id),
            approved=False,
        ).exists()

    visible_tags = ['PUBLIC']
    if is_followback or user==current_author: # if logged in user is friends with user or if logged in user viewing own profile
        visible_tags.append('FRIENDS') # show friend visibility posts
        if user==current_author: # if logged in user viewing own profile, show unlisted posts too
            visible_tags.append('UNLISTED')

    authors_posts = Post.objects.filter(author=viewing_author, visibility__in= visible_tags).exclude(description="Public Github Activity").order_by('-published') # most recent on top
    retrieve_github(viewing_author)
    github_posts = Post.objects.filter(author=viewing_author, visibility__in=visible_tags, description="Public Github Activity").order_by('-published')

    # Followers: people who follow the user
    followers_count = Follow.objects.filter(
        following=f"http://{request.get_host()}/api/authors/{author_id}",
        approved=True
    ).count()

    # Following: people the user follows
    # This returns a list of users that `author_id` is following
    followed_users = Follow.objects.filter(
        follower=f"http://{request.get_host()}/api/authors/{author_id}",
        approved=True).values_list('following', flat=True)
    following_count = followed_users.count()
    print(followed_users)

    author_url = f"http://{request.get_host()}/api/authors/{author_id}"

    # Friends: mutual follows
    friends_count = Follow.objects.filter(
        follower__in=followed_users,  # Users that are followed by `author_id`
        following=author_url,  # `author_id` is the `following`
        approved=True
    ).count()  # Count mutual follow relationships


    return render(request, "profile/profile.html", {
        'user': user,
        'posts': authors_posts,
        'ownProfile': ownProfile,
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
            Post.objects.create(
                author=user,
                title=event_type,
                description="Public Github Activity",
                visibility='PUBLIC',
                published=published_date,  # Set the published date from the activity
                text_content=post_description,
            )
    # Ends here

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def api_single_author(request, author_id):
    user = get_object_or_404(Author, id=author_id)

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
                "github": "http://github.com/" + user.github if user.github else "",
                "profileImage": user.profile_image.url if user.profile_image else None,
                "page": user.page,
                "description": user.description,
            }
            return JsonResponse(author_data, status=200)

    if request.method == 'PUT':
        serializer = AuthorProfileSerializer(user, data=request.data)

        original_github = user.github

        if serializer.is_valid():
            if original_github != serializer.validated_data.get('github'):
                Post.objects.filter(author=user, description="Public Github Activity").delete()

            serializer.save()
            author_data = {
                "type": "author",
                "id": user.id,
                "host": user.host,
                "displayName": user.display_name,
                "github": "http://github.com/" + user.github if user.github else "",
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

def edit_profile(request,author_id):
    '''
    Fetch logged in author's profile details and display them in editable inputs
    :param request:
    :param author_id: id of logged in author who is attempting to edit their own profile
    :return: html rendition of edit_profile.html with the appropriate content
    '''
    user = get_object_or_404(Author, id=author_id)
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
    author = get_object_or_404(Author, id=author_id)
    profileUserUrl = author.url  # user of the profile


    # find a diff way to do this tbh
    see_follower = request.GET.get('see_follower')
    if see_follower is None:
        follow_objects = Follow.objects.filter(follower=profileUserUrl, approved=True)
        users = [person.following for person in follow_objects if person.is_friend()]
        title = "Friends"
    else:
        if see_follower == "true":
            # use the api to get followers

            access_token = AccessToken.for_user(author)
            headers = {
                'Authorization': f'Bearer {access_token}'
            }

            responses = []
            api_url = request.build_absolute_uri(reverse('list_all_followers', kwargs={'author_id': author_id}))
            response = requests.get(api_url, headers=headers, cookies=request.COOKIES)
            print(response.json())
            responses.append(response)

            users = []
            for response in responses:
                users += response.json().get('followers', []) if response.status_code == 200 else []

            print(users)
            # for follower in users:
            #     Author.objects.update_or_create(
            #         url=follower['id'],
            #         defaults={
            #             'url': follower['id'],
            #             'host': follower['host'],
            #             'display_name': follower['displayName'],
            #             'github': follower['github'],
            #             'page': follower['page'],
            #             'profile_image': follower['profileImage'],
            #         }
            #     )
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
    return render(request, 'follower_following.html', {
        'authors': users,
        'DisplayTitle': title,
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
    author_to_follow = get_object_or_404(Author, id=author_id)


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
            "profileImage": current_author.profile_image.url if current_author.profile_image else None,
            "page": current_author.page,
        },
        "object": {
            "type": "author",
            "id": author_to_follow.url,
            "host": author_to_follow.host,
            "displayName": author_to_follow.display_name,
            "github": author_to_follow.github,
            "profileImage": author_to_follow.profile_image.url if current_author.profile_image else None,
            "page": author_to_follow.page,
        }
    }

    # access_token = AccessToken.for_user(current_author)
    # headers = {
    #     'Authorization': f'Bearer {access_token}'
    # }

    # Send the POST request to the target author's inbox endpoint
    # inbox_url = request.build_absolute_uri(reverse('inbox', args=[author_id]))
    inbox_url = author_to_follow.url + "/inbox/"
    # access_token = AccessToken.for_user(current_author)
    # headers = {
    #     'Authorization': f'Bearer {access_token}'
    # }
    # response = requests.post(inbox_url, json=follow_request, headers=headers, cookies=request.COOKIES)

    response = send_request_to_node(author_to_follow.host[:-4], inbox_url)

    if response.status_code in [200, 201]:
        print("Sent Follow request")
        print(f"Sent to: {inbox_url}")
        print(f"Response URL: {response.url}")
        messages.success(request, "Follow request sent successfully.")
    else:
        print("Failed to send Follow request")
        messages.error(request, "Failed to send follow request. Please try again.")

    return redirect('authors')

def add_external_comment(request, author_id):
    """
    Adds comment objects from an API according to
    either the 'comment' or 'comments' specification
    """
    body = json.loads(request.body)

    if body['type'] == 'comment':   # Single comment
        new_comment = Comment.objects.create(author_id=author_id,
                                             post=get_object_or_404(Post, id=body['post'].split('/')[-1]))
        serializer = CommentSerializer(new_comment, data=body)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if body['type'] == 'comments':
        for comment in body['src']:
            new_comment = Comment.objects.create(author_id=author_id, post=get_object_or_404(Post, id=body['post'].split('/')[-1]))
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
    body['author'] = author_id
    serializer = PostSerializer(data=body)
    if serializer.is_valid():
        serializer.save()
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
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
                liker = body['author']
                serializer = LikeSerializer(data=body)
                if not serializer.is_valid():
                    return Response(
                        serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST
                    )
                post_or_comment = body['object']
                if '/posts/' in post_or_comment:
                    return post_like(body)
                else:   # Comment like
                    return comment_like(body)
            # Add additional handling for other types (e.g., post, like, comment) as needed
            if body['type'] == 'post':
                return add_external_post(request, author_id)
            if body['type'] == 'comment' or body['type'] == 'comments':
                return add_external_comment(request, author_id)
        except (json.JSONDecodeError, KeyError) as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'message': 'Method not allowed'}, status=405)


    # if type = "follow":
    #     follow_author(author_id, follow_id)
    # identify the post request from the body by "type"


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
    author_to_unfollow = get_object_or_404(Author, id=author_id)

    # Get the logged-in author (assuming you have a user to author mapping)
    current_author = get_author(request) # Adjust this line to match your user-author mapping

    # Check if the follow relationship already exists
    follow_exists = Follow.objects.filter(follower=current_author.url, following=author_to_unfollow.url).exists()

    if follow_exists:
        api_url = request.build_absolute_uri(reverse('list_follower'))
        access_token = AccessToken.for_user(current_author)
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        # Make the GET request to the API endpoint
        response = requests.delete(api_url, headers=headers, cookies=request.COOKIES)

        messages.success(request, "You have successfully unfollowed this author.")

        # Create a new follow relationship
        # follow = get_object_or_404(Follow, follower=current_author.url, following=author_to_unfollow.url)
        # # Delete the Follow object to unfollow the author
        # follow.delete()
        # messages.success(request, "You have successfully unfollowed this author.")

    if not follow_exists:
        # Create a new follow relationship
        print("No follow relationship exists between these authors.")
        messages.warning(request, "You are not following this author.")

    # Redirect back to the authors list or a success page
    return redirect('authors')

def follow_requests(request, author_id):
    current_author = get_object_or_404(Author, id=author_id)  # logged in author
    print(current_author.url)
    current_follow_requests = Follow.objects.filter(following=current_author.url, approved=False)
    print(current_follow_requests)
    follower_authors = []
    for a_request in current_follow_requests:
        # follower_id = a_request.follower.replace("http://darkgoldenrod/api/authors/", "")
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
    follower_author = get_object_or_404(Author, id=follower_id)
    current_author = get_object_or_404(Author, id=author_id)
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
    follower_author = get_object_or_404(Author, id=follower_id)
    current_author = get_object_or_404(Author, id=author_id)
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
    # cleaned_friends = [int(url.replace('http://darkgoldenrod/api/authors/', '')) for url in friends]


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
    post = get_object_or_404(Post, pk=id)
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
    author = get_object_or_404(Author, id=id)

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
    post = get_object_or_404(Post, id=post_id)
    if post.author != author:
        return HttpResponseForbidden("Post cannot be edited.", status=403)

    data = request.data
    serializer = PostSerializer(post, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
        if author.host == f'http://{request.get_host()}/api/':
            # Distribute posts to connected nodes
            followers = Follow.objects.filter(following=f"{author.host}/authors/{author_id})")
            for follower in followers:
                processed_nodes = [f'http://{request.get_host()}/api/']
                if follower.host not in processed_nodes:
                    json_content = PostSerializer(post).data
                    send_request_to_node(follower.host, follower.id + '/inbox', 'POST', json_content)
                    processed_nodes.append(follower.host)
        return JsonResponse(PostSerializer(post).data)
    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def delete_post_api(request, author_id, post_id):
    author = get_author(request)
    post = get_object_or_404(Post, id=post_id)
    if post.author != author:
        return HttpResponseForbidden("Post cannot be deleted.", status=403)

    post.delete()
    return HttpResponse('Post successfully deleted.', status=204)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = get_object_or_404(Author, id=post.author_id)
    if post.visibility == "FRIENDS":
        follow = get_object_or_404(Follow, follower=author, following=post.author)
        if not follow.is_friend():
            return HttpResponse(403, 'Cannot view this post')
    return JsonResponse(get_serialized_post(post), safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_comments_from_post(request, post_url):
    post_id = post_url.split('/')[-1]
    get_comments(request, post_id)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_comments(request, author_id, post_id):
    #TO-DO: Pagination/query handling
    # page_number = request.GET.get('page', 1)
    # size = request.GET.get('size', 5)
    post = get_object_or_404(Post, id=post_id)
    # page = ((page_number - 1) * size)
    # comments = post.comment_set.all()[page:page + size]
    serializer = CommentsSerializer(post)
    return JsonResponse(serializer.data, safe=False)


def get_serialized_post(post):
    return PostSerializer(post).data


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def followers_view(request, author_id, follower_id=None):
    author = get_object_or_404(Author, id=author_id)
    follower_id = request.GET.get('follower_id')  # Get the follower_id from query params
    follower_host = request.GET.get('follower')  # Get the follower_id from query params
    print("followers_view ran initial")
    print("follower_id", follower_id)
    if request.method == 'GET':
        if follower_id:
            print("followers_view ran")
            # Decode the follower_id URL (assuming it's a URL-encoded ID)
            decoded_follower_id = unquote(follower_id)
            # Attempt to find the follower by their URL field, assuming `url_field` holds the unique URL
            id = decoded_follower_id.split('/')[-1]
            host = decoded_follower_id.replace(f'authors/{id}', '')
            print('id in function: ', id)
            print('host in function: ', host)
            follower = Author.objects.filter(host=host, id=int(id)).first()
            if not follower:
                return JsonResponse({"error": "Not Found Follower"}, status=404)
            elif not Follow.objects.filter(following=f"{author.host}authors/{author.id}", follower=f"{follower.host}authors/{follower.id}", approved=True).first():
                return JsonResponse({"error": "Not a Follower of Author"}, status=404)

            # Construct the JSON response manually
            return JsonResponse({
                "type": "author",
                "id": follower.id,
                "url": follower.url,
                "host": follower.host,
                "displayName": follower.display_name,
                "page": follower.page,
                "github": follower.github,
                "profileImage": follower.profile_image.url if follower.profile_image else ''
            })

        else:
            # Get all followers and manually construct the response
            followers_data = []
            print(author.host)
            print(author.id)
            followers = Follow.objects.filter(following=f"{author.host}authors/{author.id}", approved=True)
            followers = list(followers.values_list('follower', flat=True))
            print("followers in function", followers)
            for follower_url in followers:
                id = follower_url.split('/')[-1]
                host = follower_url.replace(f'authors/{id}', '')
                follower = Author.objects.filter(host=host, id=int(id)).first()

                followers_data.append({
                    "type": "author",
                    "id": follower.id,
                    "url": follower.url,
                    "host": follower.host,
                    "displayName": follower.display_name,
                    "page": follower.page,
                    "github": follower.github,
                    "profileImage": follower.profile_image.url if follower.profile_image else ''
                })

            return JsonResponse({
                "type": "followers",
                "followers": followers_data
            })

    elif request.method == 'PUT':
        if follower_id:
            # Decode the follower_id URL (assuming it's a URL-encoded ID)
            decoded_follower_id = unquote(follower_id)
            print(follower_id)
            # print("decoded_follower_id: ", decoded_follower_id)
            # print("author_url: ", f"{author.host}authors/{author.id}")

            follow = Follow.objects.get(follower=follower_host + "authors/" + decoded_follower_id,
                                        following=f"{author.host}authors/{author.id}")

            follow.approved = True
            follow.save()
            return JsonResponse({"status": "follow request approved"}, status=201)
        else:
            return JsonResponse({"error": "Missing foreign author ID"}, status=400)

    elif request.method == 'DELETE':
        if follower_id:
            # Decode the follower_id URL (assuming it's a URL-encoded ID)
            decoded_follower_id = unquote(follower_id)
            try:
                print("decode_follower_id: ", decoded_follower_id)
                print("author_url: ", f"{author.host}authors/{author.id}")
                follow_instance = Follow.objects.get(follower=decoded_follower_id, following=f"{author.host}authors/{author.id}")
                follow_instance.delete()
                return JsonResponse({"status": "follow relationship deleted"}, status=204)
            except Follow.DoesNotExist:
                return JsonResponse({"error": "Follow relationship not found"}, status=404)
        else:
            return JsonResponse({"error": "Missing foreign author ID"}, status=400)