from django.core import signing
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView
from .models import Post, Author, PostLike, Comment, Like, Follow, Repost, CommentLike
from django.contrib import messages
from django.db.models import Q, Count, Exists, OuterRef, Subquery
from .serializers import AuthorProfileSerializer
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
from django.contrib.auth.decorators import login_required
from .utils import get_authenticated_user_id, AuthenticationFailed
from rest_framework.response import Response
from rest_framework import status


def api_authors_list(request):
    page = int(request.GET.get('page', 1))  # Number of pages to include
    size = int(request.GET.get('size', 10))  # Number of records per page\
    query = request.GET.get('q', '')  # Search query

    # Filter authors based on the query if it exists
    if query:
        authors = Author.objects.filter(
            Q(display_name__icontains=query)
        )
    else:
        authors = Author.objects.all()

    # Use Paginator to split the queryset into pages
    paginator = Paginator(authors, size)

    # Ensure the requested page doesn't exceed total number of pages
    if page > paginator.num_pages:
        page = paginator.num_pages

    # Collect all authors up to the requested page
    author_list = []
    for i in range(1, page + 1):
        current_page = paginator.page(i)
        author_list.extend([{
            "type": "author",
            "id": f"http://darkgoldenrod/api/authors/{author.id}",
            "host": author.host,
            "display_name": author.display_name,
            "github": author.github,
            "profileImage": author.profile_image.url if author.profile_image else '',
            "page": author.page
        } for author in current_page])

    response_data = {
        "type": "authors",
        "authors": author_list,
    }

    return JsonResponse(response_data)

@api_view(['GET'])
def authors_list(request):
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)
    size = request.GET.get('size', 10)

    # Construct the URL for the API endpoint
    api_url = request.build_absolute_uri(reverse('api_authors_list'))
    api_url += f'?page={page}&size={size}'

    if query:
        api_url += f'&q={query}'

    # Make the GET request to the API endpoint
    response = requests.get(api_url)
    # print("Response: ", response)
    # print("Response text: ", response.text)
    # print("Response body: ", response.json())
    
    authors = response.json().get('authors', []) if response.status_code == 200 else []
    

    for author in authors:
        author['linkable'] = author['id'].startswith("http://darkgoldenrod/api/authors/")
        author['id'] = author['id'].split('/')[-1] if author['linkable'] else author['id']

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

def edit_post(request, post_id):
    author = get_author(request)
    post = get_object_or_404(Post, id=post_id)

    if author is None:
        return HttpResponseForbidden("You must be logged in to edit posts.")

    if post.author != author:
        return HttpResponseForbidden("You are not allowed to edit this post.")

    if request.method == 'POST':

        title = request.POST.get('title')
        text_content = request.POST.get('body-text')
        visibility = request.POST.get('visibility')

        if not title or not text_content:
            messages.error(request, "Title and description cannot be empty.")
            return render(request, 'edit_post.html', {
                'post': post,
                'author_id': author.id,
            })

        post.title = title
        post.text_content = text_content
        post.visibility = visibility
        post.published = datetime.datetime.now()
        post.save()

        return redirect('view_post', post_id=post.id)

    else:
        return render(request, 'edit_post.html', {
            'post': post,
            'author_id': author.id,
        })

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def author_posts(request, author_id):
    """
    Create a new post or return author's posts.
    """
    author = get_author(request)
    if request.method == 'POST':
        contentType = request.POST["contentType"]
        if contentType != "image":
            post = Post(title=request.POST["title"],
                        description=request.POST["description"],
                        text_content=request.POST["content"],
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
        return JsonResponse({"message": "Post created successfully"}, status=201)
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

    formatted_posts = [{
        'type': "post",
        'title': post.title,
        'id': f"http://darkgoldenrod/api/authors/{author.id}/posts/{post.id}",
        'description:': post.description,
        'contentType': post.contentType,
        'content': post.content
    } for post in posts]

def delete_post(request, post_id):
    author = get_author(request)
    post = get_object_or_404(Post, id=post_id)

    if post.author != author:
        return HttpResponseForbidden("You are not allowed to delete this post.")

    if request.method == 'POST':
        # Set the visibility to 'DELETED'
        post.visibility = 'DELETED'
        post.save()
        messages.success(request, "Post has been deleted.")
        return redirect('index')


def post_like(request, id):
    """
    Method for liking a post given an ID
    If already liked by requesting author, unlike
    """
    author = get_author(request)
    post = get_object_or_404(Post, pk=id)
    if PostLike.objects.filter(owner=post, liker=author).exists():
        PostLike.objects.filter(owner=post, liker=author).delete()
    else:
        new_like = PostLike(owner=post, liker=author)
        new_like.save()
    return(redirect(f'/node/posts/{id}/'))

def comment_like(request, id):
    """
    Method for liking a comment given comment ID
    if already liked by requesting author, removes the like
    """
    author = get_author(request)
    comment = get_object_or_404(Comment, pk=id)
    post = get_object_or_404(Post, pk=comment.post.id)
    if CommentLike.objects.filter(owner=comment, liker=author).exists():
        CommentLike.objects.filter(owner=comment, liker=author).delete()
    else:
        new_like = CommentLike(owner=comment, liker=author)
        new_like.save()
    return(redirect(f'/node/posts/{post.id}/'))

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
        if post.visibility == "FRIENDS" or post.visibility == "UNLISTED":
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
    user = get_object_or_404(Author, id=author_id)
    current_author = get_author(request) # logged in author
    ownProfile = (user == current_author)

    is_following = Follow.objects.filter( # if logged in author following the user
        follower="http://darkgoldenrod/api/authors/" + str(current_author.id),
        following="http://darkgoldenrod/api/authors/" + str(author_id),
        approved=True,
    ).exists()
    if is_following:
        is_followback = Follow.objects.filter(  # ... see if user is following back
            follower="http://darkgoldenrod/api/authors/" + str(author_id),
            following="http://darkgoldenrod/api/authors/" + str(current_author.id),
            approved=True,
        ).exists()
        is_pending = False
    else:
        is_followback = False
        is_pending = Follow.objects.filter( # if logged in author following the user
            follower="http://darkgoldenrod/api/authors/" + str(current_author.id),
            following="http://darkgoldenrod/api/authors/" + str(author_id),
            approved=False,
        ).exists()

    visible_tags = ['PUBLIC']
    if is_followback or user==current_author: # if logged in user is friends with user or if logged in user viewing own profile
        visible_tags.append('FRIENDS') # show friend visibility posts
        if user==current_author: # if logged in user viewing own profile, show unlisted posts too
            visible_tags.append('UNLISTED')
    authors_posts = Post.objects.filter(author=user, visibility__in= visible_tags).exclude(description="Public Github Activity").order_by('-published') # most recent on top
    retrieve_github(user)
    github_posts = Post.objects.filter(author=user, visibility__in=visible_tags, description="Public Github Activity").order_by('-published')

    response_data = {
        'user': {
            'id': user.id,
            'profile photo': user.profile_image,
            'display name': user.display_name,
            'description': user.description,
            'github': user.github,
        },
        'posts': [
            {
                'id': post.id,
                'title': post.title,
                'description': post.description,
                # 'content': post.content,
                'published': post.published,
                'visibility': post.visibility,
            } for post in authors_posts
        ],
        'activity': [
            {
                'id': post.id,
                'title': post.title,
                'description': post.description,
                # 'content': post.content,
                'published': post.published,
                'visibility': post.visibility,
            } for post in github_posts
        ],
    }

    return render(request, "profile/profile.html", {
        'user': user,
        'posts': authors_posts,
        'ownProfile': ownProfile,
        'is_following': is_following,
        'is_pending': is_pending,
        'activity': github_posts,
    })

def retrieve_github(user):
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

def view_edit_profile(request,author_id):
    user = get_object_or_404(Author, id=author_id)
    serializer = AuthorProfileSerializer(user)
    return render(request, 'profile/edit_profile.html', {'user': serializer.data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit_profile(request, author_id):
    user = get_object_or_404(Author, id=author_id)

    if request.method == 'POST':
        original_github = user.github
        serializer = AuthorProfileSerializer(user, data=request.data)  # This should handle multipart/form-data

        if serializer.is_valid():
            # Check for changes in GitHub username
            if original_github != serializer.validated_data.get('github'):
                Post.objects.filter(author=user, description="Public Github Activity").delete()

            serializer.save()

            return JsonResponse(serializer.data, status=200)

@api_view(['GET'])
def followers_following(request, author_id):
    profileUserUrl = "http://darkgoldenrod/api/authors/" + str(author_id)  # user of the profile

    # find a diff way to do this tbh
    see_follower = request.GET.get('see_follower', 'true') == 'true'

    if see_follower:
        # Get all followers by checking the Follow model
        users = Follow.objects.filter(following=profileUserUrl, approved=True).values_list('follower', flat=True)
        title = "Followers"
    else:
        users = Follow.objects.filter(follower=profileUserUrl, approved=True).values_list('following', flat=True)
        title = "Followings"

    user_ids = [url.replace("http://darkgoldenrod/api/authors/", "") for url in users]
    user_authors = Author.objects.filter(id__in=user_ids)

    # serialize
    author_data = [{'id': author.id, 'display_name': author.display_name} for author in user_authors]

    if request.accepted_renderer.format == 'json':
        author_data = [{'id': author.id, 'display_name': author.display_name} for author in user_authors]
        return Response({
            'title': title,
            'authors': author_data
        })
    return render(request, 'follower_following.html', {
        'authors': user_authors,
        'DisplayTitle': title
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
            "id": f"http://darkgoldenrod/api/authors/{current_author.id}",
            "host":"http://darkgoldenrod/api/",
            "displayName": current_author.display_name,
            "github": current_author.github,
            "profileImage": current_author.profile_image.url if current_author.profile_image else None,
            "page": current_author.page,
        },
        "object": {
            "type": "author",
            "id": f"http://darkgoldenrod/api/authors/{author_to_follow.id}",
            "host":"http://darkgoldenrod/api/",
            "displayName": author_to_follow.display_name,
            "github": author_to_follow.github,
            "profileImage": author_to_follow.profile_image.url if current_author.profile_image else None,
            "page": author_to_follow.page,
        }
    }

    # Send the POST request to the target author's inbox endpoint
    inbox_url = request.build_absolute_uri(reverse('inbox', args=[author_id]))
    response = requests.post(inbox_url, json=follow_request)

    if response.status_code in [200, 201]:
        print("Sent Follow request")
        print(f"Sent to: {inbox_url}")
        print(f"Response URL: {response.url}")
        messages.success(request, "Follow request sent successfully.")
    else:
        print("Failed to send Follow request")
        messages.error(request, "Failed to send follow request. Please try again.")

    return redirect('authors')

@csrf_exempt
def inbox(request, author_id):
    print("Inbox function ran")
    if request.method == 'POST':
        try:
            print("Inbox POST request received")
            # Parse the request body
            body = json.loads(request.body)
            print("Request body:", body)
            if body['type'] == 'follow':
                # Extract relevant information and call follow_author
                follower = body['actor']
                following = body['object']
                print("Follow request type detected")
                return follow_author(follower, following)
            # Add additional handling for other types (e.g., post, like, comment) as needed
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({'error': 'Invalid request format'}, status=400)
    
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
        Follow.objects.create(follower=follower_url, following=following_url)
        
        return JsonResponse({'message': 'Follow request processed successfully'}, status=200)
    else:
        return JsonResponse({'message': 'Follow relationship already exists'}, status=400)

# With help from Chat-GPT 4o, OpenAI, 2024-10-14
@permission_classes([IsAuthenticated])
def unfollow_author(request, author_id):
    # Get the author being followed
    author_to_unfollow = get_object_or_404(Author, id=author_id).id

    # Get the logged-in author (assuming you have a user to author mapping)
    current_author = get_author(request).id # Adjust this line to match your user-author mapping

    # Check if the follow relationship already exists
    follow_exists = Follow.objects.filter(follower="http://darkgoldenrod/api/authors/" + str(current_author), following="http://darkgoldenrod/api/authors/" + str(author_to_unfollow)).exists()

    if follow_exists:
        # Create a new follow relationship
        follow = get_object_or_404(Follow, follower="http://darkgoldenrod/api/authors/" + str(current_author), following="http://darkgoldenrod/api/authors/" + str(author_to_unfollow))
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
    current_author = get_object_or_404(Author, id=author_id)  # logged in author
    current_follow_requests = Follow.objects.filter(following="http://darkgoldenrod/api/authors/" + str(current_author.id), approved=False)

    follower_authors = []
    for a_request in current_follow_requests:
        follower_id = a_request.follower.replace("http://darkgoldenrod/api/authors/", "")
        follower_author = get_object_or_404(Author, id=follower_id)
        follower_authors.append(follower_author)

    return render(request, 'follow_requests.html', {
        'follow_authors': follower_authors,
        'author': current_author,
    })

def approve_follow(request, author_id, follower_id):
    follow_request = get_object_or_404(Follow, follower="http://darkgoldenrod/api/authors/" + str(follower_id), following = "http://darkgoldenrod/api/authors/" + str(author_id))
    follow_request.approved = True
    follow_request.save()
    return redirect('follow_requests', author_id=author_id)  # Redirect to the profile view after saving

def decline_follow(request, author_id, follower_id):
    follow_request = get_object_or_404(Follow, follower="http://darkgoldenrod/api/authors/" + str(follower_id), following = "http://darkgoldenrod/api/authors/" + str(author_id))
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
    current_author = get_author(request).id

    # Get filter option from URL query parameters (default is 'all')
    filter_option = request.GET.get('filter', 'all')

    # Get the authors that the current user is following
    follow_objects = Follow.objects.filter(follower="http://darkgoldenrod/api/authors/" + str(current_author), approved=True)


    followings = list(follow_objects.values_list('following', flat=True))
    cleaned_followings = [int(url.replace('http://darkgoldenrod/api/authors/', '')) for url in followings]

    friends = [follow.following for follow in follow_objects if follow.is_friend()]
    cleaned_friends = [int(url.replace('http://darkgoldenrod/api/authors/', '')) for url in friends]


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
            "shared_date": repost.shared_date
        })
    
    # print(f"Current Author ID: {current_author}|")  # Debug the current author's ID
    # follower_url = "http://darkgoldenrod/api/authors/" + str(current_author)
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
                "url": reverse("view_post", kwargs={"post_id": post.id})
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
