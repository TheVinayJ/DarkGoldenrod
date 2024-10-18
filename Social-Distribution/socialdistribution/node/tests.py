from http.client import responses

from django.contrib.sessions.models import Session
from django.core import signing
from django.urls import reverse

from .models import *
from django.test import TestCase, Client
from . import views


class PostTests(TestCase):

    def setUp(self):

        self.author = Author.objects.create(display_name="Test Author")
        self.post = Post.objects.create(
            title="Test Title",
            description="Test Description",
            text_content="Test Content",
            author=self.author,
            visibility="PUBLIC"
        )

        self.client = Client()

        signed_id = signing.dumps(self.author.id)
        self.client.cookies['id'] = signed_id

    def test_post_creation(self):
            self.assertEqual(self.post.title, "Test Title")
            self.assertEqual(self.post.author.display_name, "Test Author")

    def test_add_post(self):
            response = self.client.get(reverse('add'), follow=True)
            self.assertEqual(response.status_code, 200)
            response = self.client.post(reverse(views.save), {'title': 'New Post',
                                                          'body-text': 'Test Description',
                                                          'visibility': 'PUBLIC'})
            self.assertEqual(response.status_code, 302)
            self.assertTrue(Post.objects.filter(title="New Post").exists())

    def test_like_post(self):
        test_post_id = self.post.id
        self.assertFalse(PostLike.objects.filter(post=self.post).exists())
        response = self.client.post(reverse(views.post_like), test_post_id, follow=True)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(PostLike.objects.filter(post=self.post).exists())