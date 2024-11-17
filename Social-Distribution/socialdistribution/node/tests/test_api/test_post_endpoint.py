from xml.dom.minidom import Comment

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from node.models import Author, Post, AllowedNode, Comment
from node.views import add_external_comment
from django.contrib.auth import get_user_model
from node.serializers import AuthorSerializer
from base64 import b64encode
import json
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class PostsApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create a test author
        self.author = User.objects.create_user(id=1, display_name="Test Author1", description="Test Description",
                                                github="torvalds", email="author1@test.com", password="pass")

        self.other = User.objects.create_user(id=2, display_name="Test Author2", email="author2@test.com", password="pass")

        self.node = AllowedNode.objects.create(
            url="http://localhost:8000/",
            username="nodeuser",
            password="nodepassword",
            is_active=True
        )

        # Set up Basic Auth headers
        valid_credentials = b64encode(b'nodeuser:nodepassword').decode('utf-8')
        self.auth_headers = {'HTTP_AUTHORIZATION': f'Basic {valid_credentials}'}

        # Create a sample public post
        self.public_post = Post.objects.create(
            title="Public Post",
            description="A public post description",
            contentType="text/plain",
            text_content="This is a public post",
            author=self.author,
            published=timezone.now(),
            visibility="PUBLIC",
        )

        # Create a sample friends-only post
        self.friends_post = Post.objects.create(
            title="Friends-Only Post",
            description="A friends-only post description",
            contentType="text/plain",
            text_content="This is a friends-only post",
            author=self.author,
            published=timezone.now(),
            visibility="FRIENDS",
        )

    # def test_get_public_post(self):
    #     """Test retrieving a public post by its ID."""
    #     self.client.force_authenticate(user=self.author)
    #
    #     url = f"http://localhost:8000/api/authors/{self.author.id}/posts/{self.public_post.id}"
    #     response = self.client.get(url)
    #
    #     # Assert response
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.data['type'], "post")
    #     self.assertEqual(response.data['title'], self.public_post.title)
    #     self.assertEqual(response.data['id'], self.public_post.id)
    #     self.assertEqual(response.data['page'], "http://localhost:8000/authors/1/posts/1")
    #     self.assertEqual(response.data['published'], self.public_post.published)
    #     self.assertEqual(response.data['visibility'], "PUBLIC")
    #
    # def test_get_friends_post_requires_authentication(self):
    #     """Test retrieving a friends-only post requires authentication."""
    #     self.client.force_authenticate(user=self.author)
    #
    #     url = f"http://localhost:8000/api/authors/{self.author.id}/posts/{self.friends_post.id}"
    #     response = self.client.get(url)
    #
    #     # Assert response without authentication returns 403
    #     self.assertEqual(response.status_code, 403)
    #
    #     # Send request with authentication headers
    #     response = self.client.get(url, **self.auth_headers)
    #
    #     # Assert response
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.data['type'], "post")
    #     self.assertEqual(response.data['title'], self.friends_post.title)
    #     self.assertEqual(response.data['visibility'], "FRIENDS")

    # def test_update_post(self):
    #     """Test updating an existing post (requires authentication as author)."""
    #     url = f"http://localhost:8000/api/authors/{self.author.id}/posts/{self.public_post.id}"
    #     updated_data = {
    #         "title": "Updated Public Post Title",
    #         "description": "Updated description",
    #         "content": "Updated content for the public post",
    #         "contentType": "text/plain",
    #         "visibility": "PUBLIC",
    #     }
    #
    #     response = self.client.put(url, data=json.dumps(updated_data), content_type="application/json", **self.auth_headers)
    #
    #     # Assert response
    #     self.assertEqual(response.status_code, 200)
    #     self.public_post.refresh_from_db()
    #     self.assertEqual(self.public_post.title, updated_data["title"])
    #     self.assertEqual(self.public_post.description, updated_data["description"])
    #     self.assertEqual(self.public_post.content, updated_data["content"])
    #
    # def test_delete_post(self):
    #     """Test deleting a post (requires authentication as author)."""
    #     url = f"http://localhost:8000/api/authors/{self.author.id}/posts/{self.public_post.id}"
    #     response = self.client.delete(url, **self.auth_headers)
    #
    #     # Assert response
    #     self.assertEqual(response.status_code, 204)
    #     self.assertFalse(Post.objects.filter(id=self.public_post.id).exists())
    #
    # def test_get_recent_posts_paginated(self):
    #     """Test retrieving recent posts of an author (paginated)."""
    #     self.client.force_authenticate(user=self.author)
    #     # Add extra posts for pagination
    #     for i in range(15):
    #         Post.objects.create(
    #             title=f"Post {i}",
    #             description=f"Description of post {i}",
    #             contentType="text/plain",
    #             content="Content",
    #             author=self.author,
    #             published=timezone.now() - timedelta(days=i),
    #             visibility="PUBLIC",
    #         )
    #
    #     # Retrieve paginated posts
    #     url = f"/service/api/authors/{self.author.id}/posts?page=1&size=5"
    #     response = self.client.get(url)
    #
    #     # Assert response
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.data["type"], "posts")
    #     self.assertEqual(response.data["size"], 5)
    #     self.assertEqual(len(response.data["src"]), 5)
    #
    # def test_create_new_post(self):
    #     """Test creating a new post for an author."""
    #     self.client.force_authenticate(user=self.author)
    #
    #     url = f"http://localhost:8000/api/authors/{self.author.id}/posts/"
    #     new_post_data = {
    #         "title": "New Post Title",
    #         "description": "New post description",
    #         "contentType": "text/plain",
    #         "content": "This is the content of the new post",
    #         "visibility": "PUBLIC",
    #     }
    #
    #     response = self.client.post(url, data=json.dumps(new_post_data), content_type="application/json", **self.auth_headers)
    #
    #     # Assert response
    #     self.assertEqual(response.status_code, 201)
    #     created_post = Post.objects.get(title=new_post_data["title"])
    #     self.assertEqual(created_post.description, new_post_data["description"])
    #     self.assertEqual(created_post.content, new_post_data["content"])
    #     self.assertEqual(created_post.visibility, new_post_data["visibility"])

    def test_inbox_post(self):
        self.client.force_authenticate(user=self.author)
        url = f"http://localhost:8000/api/authors/{self.author.id}/inbox/"
        data = {
            "type": 'post',
            'title': 'inbox title',
            'description': 'inbox description',
            'id': f'http://localhost:8000/api/authors/{self.author.id}/posts/2',
            'page': f'http://localhost:8000/authors/{self.author.id}/posts/2',
            'contentType': 'text/plain',
            'content': 'inbox text',
            'visibility': 'PUBLIC',
            'author': AuthorSerializer(self.author).data,
            'comments': {},
            'likes':{},
            'published': str(timezone.now()),
        }
        data = json.dumps(data)

        response = self.client.post(url, data=data, content_type='application/json', **self.auth_headers)
        print(response.content)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Post.objects.filter(title='inbox title').count(), 1)

    def test_forbidden_edits(self):
        self.client.force_authenticate(user=self.other)
        url = f"/api/authors/{self.author.id}/posts/{self.public_post.id}"
        new_post_data = {
            "title": "Edited Post Title",
            "description": "Edited post description",
            "content": "Edited content"
        }
        response = self.client.put(url, data=new_post_data, format='json', **self.auth_headers)
        self.public_post.refresh_from_db()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.public_post.title, "Public Post")
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Post.objects.filter(id=self.public_post.id).exists())

    def test_edit_post(self):
        self.client.force_authenticate(user=self.author)
        url = f"/api/authors/{self.author.id}/posts/{self.public_post.id}"
        new_post_data = {
            "title": "Edited Post Title",
            "description": "Edited post description",
            "content": "Edited content"
        }
        response = self.client.put(url, data=new_post_data, format='json', **self.auth_headers)
        self.public_post.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.public_post.title, "Edited Post Title")

    def test_add_comment_inbox(self):
        self.client.force_authenticate(user=self.author)
        url = f"http://localhost:8000/api/authors/{self.author.id}/inbox/"
        data = {
            'type': 'comment',
            'author': AuthorSerializer(self.author).data,
            'comment': 'New comment',
            'contentType': 'text/plain',
            'published': str(timezone.now()),
            'id': f'http://darkgoldenrod/api/authors/{self.author}/commented/1',
            'post': f'http://darkgoldenrod/api/authors/{self.author.id}/posts/{self.public_post.id}',
            'likes': {},
        }
        data=json.dumps(data)

        self.assertEqual(Comment.objects.filter(post=self.public_post.id).count(), 0)
        response = self.client.post(url, data=data, content_type='application/json', **self.auth_headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Comment.objects.filter(post=self.public_post.id).count(), 1)

    def test_delete_post_API(self):
        self.client.force_authenticate(user=self.author)
        url = f'/api/authors/{self.author.id}/posts/{self.public_post.id}'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Post.objects.filter(id=self.public_post.id).exists())
