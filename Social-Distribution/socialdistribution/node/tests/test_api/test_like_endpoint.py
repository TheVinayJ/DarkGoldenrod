from django.test import TestCase
from rest_framework.test import APIClient, APITestCase
from node.models import Author, Post, Comment, Like
from base64 import b64encode
from django.utils import timezone
import json
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class LikesApiTest(APITestCase):
    def setUp(self):
        self.client = APIClient()

        # Create test authors
        self.author_1 = User.objects.create_user(id=1, display_name="Test Author1", description="Test Description",
                                                github="torvalds", email="author1@test.com", password="pass")

        self.author_2 = User.objects.create_user(id=2, display_name="Test Author2", email="author2@test.com",
                                                password="pass")

        # Set up Basic Auth headers
        valid_credentials = b64encode(b'author1@example.com:password').decode('utf-8')
        self.auth_headers = {'HTTP_AUTHORIZATION': f'Basic {valid_credentials}'}

        # Create a sample post by author_1
        self.post = Post.objects.create(
            title="Sample Post",
            description="This is a sample post description",
            contentType="text/plain",
            author=self.author_1,
            published=timezone.now(),
            visibility="PUBLIC",
        )

        self.comment = Comment.objects.create(
            text="This is a sample comment",
            author=self.author_2,
            post=self.post,
            published=timezone.now(),
        )

    def test_post_like_to_inbox(self):
        """Test posting an invalid like object to inbox."""
        inbox_url = reverse('inbox', args=[self.author_1.id])
        invalid_like_data = {
            "type": "like",
            # Missing required fields
            "author": {},
            "object": "invalid_url"
        }
        
        print(f"Testing URL: {inbox_url}")  # Debug print
        response = self.client.post(
            inbox_url, 
            data=json.dumps(invalid_like_data), 
            content_type="application/json", 
            **self.auth_headers
        )
        print(f"Response Status: {response.status_code}")  # Debug print
        print(f"Response Content: {response.content}")     # Debug print
        print(f"Final URL after potential redirect: {response.url}")  # Debug print if there was a redirect
        
        self.assertEqual(response.status_code, 400)
        # inbox_url = f"/service/api/authors/{self.author_1.id}/inbox"
        # like_data = {
        #     "type": "like",
        #     "author": {
        #         "type": "author",
        #         "id": f"http://nodeaaaa/api/authors/{self.author_2.id}",
        #         "displayName": self.author_2.display_name,
        #         "github": self.author_2.github,
        #         "profileImage": self.author_2.profile_image,
        #         "page": f"http://nodeaaaa/authors/{self.author_2.id}"
        #     },
        #     "published": timezone.now().isoformat(),
        #     "id": f"http://nodeaaaa/api/authors/{self.author_2.id}/liked/{self.post.id}",
        #     "object": f"http://nodeaaaa/api/authors/{self.author_1.id}/posts/{self.post.id}"
        # }

        # response = self.client.post(inbox_url, data=json.dumps(like_data), content_type="application/json", **self.auth_headers)

        # # Assert response
        # self.assertEqual(response.status_code, 201)

        

    def test_get_likes_on_post(self):
        """Test retrieving likes on a specific post."""
        # Add a like on the post by author_2
        Like.objects.create(
            author=self.author_2,
            object=self.post,
            published=timezone.now()
        )

        likes_url = f"/service/api/authors/{self.author_1.id}/posts/{self.post.id}/likes"
        response = self.client.get(likes_url)

        # Assert response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["type"], "likes")
        self.assertGreaterEqual(len(response.data["src"]), 1)
        self.assertEqual(response.data["src"][0]["author"]["id"], f"http://nodeaaaa/api/authors/{self.author_2.id}")

    def test_get_likes_on_comment(self):
        """Test retrieving likes on a specific comment."""
        # Add a like on the comment by author_1
        Like.objects.create(
            author=self.author_1,
            object=self.comment,
            published=timezone.now()
        )

        likes_url = f"/service/api/authors/{self.author_1.id}/posts/{self.post.id}/comments/{self.comment.id}/likes"
        response = self.client.get(likes_url)

        # Assert response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["type"], "likes")
        self.assertGreaterEqual(len(response.data["src"]), 1)
        self.assertEqual(response.data["src"][0]["author"]["id"], f"http://nodeaaaa/api/authors/{self.author_1.id}")

    def test_get_things_liked_by_author(self):
        """Test retrieving things liked by a specific author."""
        # Add likes by author_1 on a post and a comment
        Like.objects.create(
            author=self.author_1,
            object=self.post,
            published=timezone.now()
        )
        Like.objects.create(
            author=self.author_1,
            object=self.comment,
            published=timezone.now()
        )

        liked_url = f"/service/api/authors/{self.author_1.id}/liked"
        response = self.client.get(liked_url)

        # Assert response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["type"], "likes")
        self.assertGreaterEqual(len(response.data["src"]), 2)

    def test_get_specific_like(self):
        """Test retrieving a specific like by its ID."""
        # Add a like by author_2 on the post
        like = Like.objects.create(
            author=self.author_2,
            object=self.post,
            published=timezone.now()
        )

        specific_like_url = f"/service/api/authors/{self.author_2.id}/liked/{like.id}"
        response = self.client.get(specific_like_url)

        # Assert response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["type"], "like")
        self.assertEqual(response.data["author"]["id"], f"http://nodeaaaa/api/authors/{self.author_2.id}")
        self.assertEqual(response.data["object"], f"http://nodeaaaa/api/authors/{self.author_1.id}/posts/{self.post.id}")