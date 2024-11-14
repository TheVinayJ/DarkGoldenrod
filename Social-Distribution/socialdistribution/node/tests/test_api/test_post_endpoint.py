from django.test import TestCase
from rest_framework.test import APIClient
from node.models import Author, Post  # Assuming models for Author and Post exist
from base64 import b64encode
import json
from django.utils import timezone
from datetime import timedelta

class PostsApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create a test author
        self.author = Author.objects.create(
            email="author@example.com",
            display_name="Test Author",
            github="http://github.com/testauthor",
            profile_image="https://i.imgur.com/k7XVwpB.jpeg"
        )

        # Set up Basic Auth headers
        valid_credentials = b64encode(b'author@example.com:password').decode('utf-8')
        self.auth_headers = {'HTTP_AUTHORIZATION': f'Basic {valid_credentials}'}

        # Create a sample public post
        self.public_post = Post.objects.create(
            title="Public Post",
            description="A public post description",
            contentType="text/plain",
            content="This is a public post",
            author=self.author,
            published=timezone.now(),
            visibility="PUBLIC",
        )

        # Create a sample friends-only post
        self.friends_post = Post.objects.create(
            title="Friends-Only Post",
            description="A friends-only post description",
            contentType="text/plain",
            content="This is a friends-only post",
            author=self.author,
            published=timezone.now(),
            visibility="FRIENDS",
        )

    def test_get_public_post(self):
        """Test retrieving a public post by its ID."""
        url = f"/service/api/authors/{self.author.id}/posts/{self.public_post.id}"
        response = self.client.get(url)

        # Assert response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['type'], "post")
        self.assertEqual(response.data['title'], self.public_post.title)
        self.assertEqual(response.data['visibility'], "PUBLIC")

    def test_get_friends_post_requires_authentication(self):
        """Test retrieving a friends-only post requires authentication."""
        url = f"/service/api/authors/{self.author.id}/posts/{self.friends_post.id}"
        response = self.client.get(url)

        # Assert response without authentication returns 403
        self.assertEqual(response.status_code, 403)

        # Send request with authentication headers
        response = self.client.get(url, **self.auth_headers)

        # Assert response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['type'], "post")
        self.assertEqual(response.data['title'], self.friends_post.title)
        self.assertEqual(response.data['visibility'], "FRIENDS")

    def test_update_post(self):
        """Test updating an existing post (requires authentication as author)."""
        url = f"/service/api/authors/{self.author.id}/posts/{self.public_post.id}"
        updated_data = {
            "title": "Updated Public Post Title",
            "description": "Updated description",
            "content": "Updated content for the public post",
            "contentType": "text/plain",
            "visibility": "PUBLIC",
        }

        response = self.client.put(url, data=json.dumps(updated_data), content_type="application/json", **self.auth_headers)

        # Assert response
        self.assertEqual(response.status_code, 200)
        self.public_post.refresh_from_db()
        self.assertEqual(self.public_post.title, updated_data["title"])
        self.assertEqual(self.public_post.description, updated_data["description"])
        self.assertEqual(self.public_post.content, updated_data["content"])

    def test_delete_post(self):
        """Test deleting a post (requires authentication as author)."""
        url = f"/service/api/authors/{self.author.id}/posts/{self.public_post.id}"
        response = self.client.delete(url, **self.auth_headers)

        # Assert response
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Post.objects.filter(id=self.public_post.id).exists())

    def test_get_recent_posts_paginated(self):
        """Test retrieving recent posts of an author (paginated)."""
        # Add extra posts for pagination
        for i in range(15):
            Post.objects.create(
                title=f"Post {i}",
                description=f"Description of post {i}",
                contentType="text/plain",
                content="Content",
                author=self.author,
                published=timezone.now() - timedelta(days=i),
                visibility="PUBLIC",
            )

        # Retrieve paginated posts
        url = f"/service/api/authors/{self.author.id}/posts?page=1&size=5"
        response = self.client.get(url)

        # Assert response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["type"], "posts")
        self.assertEqual(response.data["size"], 5)
        self.assertEqual(len(response.data["src"]), 5)

    def test_create_new_post(self):
        """Test creating a new post for an author."""
        url = f"/service/api/authors/{self.author.id}/posts/"
        new_post_data = {
            "title": "New Post Title",
            "description": "New post description",
            "contentType": "text/plain",
            "content": "This is the content of the new post",
            "visibility": "PUBLIC",
        }

        response = self.client.post(url, data=json.dumps(new_post_data), content_type="application/json", **self.auth_headers)

        # Assert response
        self.assertEqual(response.status_code, 201)
        created_post = Post.objects.get(title=new_post_data["title"])
        self.assertEqual(created_post.description, new_post_data["description"])
        self.assertEqual(created_post.content, new_post_data["content"])
        self.assertEqual(created_post.visibility, new_post_data["visibility"])