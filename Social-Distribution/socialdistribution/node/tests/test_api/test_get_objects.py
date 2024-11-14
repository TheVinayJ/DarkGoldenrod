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

        post = views.get_serialized_post(self.post)
        self.assertEqual(post['comments']['count'], 1)

        response = self.client.get(reverse('get_comments', args=[self.post.author.id, self.post.id]))
        self.assertTrue(response.json() == post['comments'])

    def test_get_post_with_like(self):

        self.client.force_authenticate(user=self.user)

        self.new_like = PostLike.objects.create(
            liker=self.author,
            owner=self.post,
        )

        post = views.get_serialized_post(self.post)
        self.assertEqual(post['likes']['count'], 1)

        response = self.client.get(reverse('get_likes', args=[self.post.id]))
        self.assertTrue(response.json() == post['likes'])

    def test_get_post_endpoint(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse('get_post', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
