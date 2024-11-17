from django.test import TestCase
from rest_framework.test import APIClient
from node.models import Author, Post, Comment
from base64 import b64encode
from django.utils import timezone
import json
from django.contrib.auth import get_user_model

User = get_user_model()

class CommentsApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create a test author
        self.author1 = User.objects.create_user(id=1, display_name="Test Author1", description="Test Description",
                                               github="torvalds", email="author1@test.com", password="pass")

        self.author2 = User.objects.create_user(id=2, display_name="Test Author2", email="author2@test.com",
                                              password="pass")

        # Set up authentication headers
        valid_credentials = b64encode(b'author1@example.com:password').decode('utf-8')
        self.auth_headers = {'HTTP_AUTHORIZATION': f'Basic {valid_credentials}'}

        # Create a sample post by author_1
        self.post = Post.objects.create(
            title="Sample Post",
            description="This is a sample post description",
            contentType="text/plain",
            text_content="Sample post content",
            author=self.author_1,
            published=timezone.now(),
            visibility="PUBLIC",
        )

        # Create a sample comment on the post by author_2
        self.comment = Comment.objects.create(
            text="This is a sample comment",
            author=self.author_2,
            post=self.post,
            published=timezone.now(),
        )

    def test_post_comment_to_inbox(self):
        """Test posting a comment to the author's inbox."""
        inbox_url = f"http://localhost:8000/api/authors/{self.author_1.id}/inbox/"
        comment_data = {
            "type": "comment",
            "author": {
                "type": "author",
                "id": f"http://nodeaaaa/api/authors/{self.author_2.id}",
                "displayName": self.author_2.display_name,
                "github": self.author_2.github,
                "profileImage": self.author_2.profile_image,
                "page": f"http://nodeaaaa/authors/{self.author_2.id}"
            },
            "comment": "This is a new comment in the inbox",
            "contentType": "text/markdown",
            "published": timezone.now().isoformat(),
            "post": f"http://nodeaaaa/api/authors/{self.author_1.id}/posts/{self.post.id}"
        }

        response = self.client.post(inbox_url, data=json.dumps(comment_data), content_type="application/json", **self.auth_headers)
        
        # Assert response
        self.assertEqual(response.status_code, 201)

    def test_get_comments_on_post(self):
        """Test retrieving comments on a specific post."""
        comments_url = f"http://localhost:8000/api/authors/{self.author_1.id}/posts/{self.post.id}/comments/"
        response = self.client.get(comments_url)

        # Assert response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["type"], "comments")
        self.assertEqual(len(response.data["src"]), 1)
        self.assertEqual(response.data["src"][0]["comment"], self.comment.comment)
        self.assertEqual(response.data["src"][0]["author"]["id"], f"http://nodeaaaa/api/authors/{self.author_2.id}")

    def test_get_specific_comment(self):
        """Test retrieving a specific comment by its full ID."""
        encoded_comment_id = f"http://nodeaaaa/api/authors/{self.author_2.id}/commented/{self.comment.id}".replace("/", "%2F")
        comment_url = f"/service/api/authors/{self.author_1.id}/posts/{self.post.id}/comments/{encoded_comment_id}/"

        response = self.client.get(comment_url)
        
        # Assert response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["type"], "comment")
        self.assertEqual(response.data["comment"], self.comment.comment)
        self.assertEqual(response.data["author"]["id"], f"http://nodeaaaa/api/authors/{self.author_2.id}")

    def test_get_comments_by_author(self):
        """Test retrieving a list of comments made by a specific author."""
        comments_list_url = f"http://localhost:8000/api/authors/{self.author_2.id}/commented/"

        response = self.client.get(comments_list_url)

        # Assert response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["type"], "comments")
        self.assertGreaterEqual(len(response.data["src"]), 1)
        self.assertEqual(response.data["src"][0]["comment"], self.comment.comment)
        self.assertEqual(response.data["src"][0]["post"], f"http://nodeaaaa/api/authors/{self.author_1.id}/posts/{self.post.id}")