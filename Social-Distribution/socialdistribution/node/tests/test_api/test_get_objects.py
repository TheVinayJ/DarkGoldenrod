import datetime
import sys

from django.contrib.auth import login
from django.utils import timezone

sys.path.append('../node')

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from node.models import Post, Comment, PostLike, CommentLike, Author
from node.serializers import PostSerializer
from node import views

class GetObjectTests(TestCase):
    def setUp(self):

        self.user = Author.objects.create(display_name='testuser', password='password', email='email@test.com')
        self.client = APIClient()

        self.author = Author.objects.create(display_name="Test Author",
                                            email='testAuthor@test.com',
                                            password='password')

        self.post = Post.objects.create(
            title="Test Title",
            description="Test Description",
            contentType="text/plain",
            text_content="Test Content",
            author=self.author,
            visibility="PUBLIC",
            published=timezone.make_aware(datetime.datetime.now(), datetime.timezone.utc),
        )

    def test_get_post_object(self):
        response = views.get_serialized_post(self.post)
        self.assertEqual(response['title'], self.post.title)
        self.assertEqual(response['description'], self.post.description)
        self.assertEqual(response['contentType'], self.post.contentType)
        self.assertEqual(response['content'], self.post.text_content)

    def test_get_post_with_comment(self):

        self.client.force_authenticate(user=self.user)

        self.new_comment = Comment.objects.create(
            author=self.author,
            post=self.post,
            text="Test Comment",
        )

        response = views.get_serialized_post(self.post)
        self.assertEqual(response['comments']['count'], 1)
