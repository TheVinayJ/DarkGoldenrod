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

        self.comment = Comment.objects.create(
            author=self.author,
            post=self.post,
            text="Test Comment text"
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
        self.assertFalse(PostLike.objects.filter(owner=self.post).exists())
        response = self.client.post(reverse('like', args=[test_post_id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PostLike.objects.filter(owner=self.post).exists())

    def test_unlike_post(self):
        test_post_id = self.post.id
        self.assertFalse(PostLike.objects.filter(owner=self.post).exists())
        response = self.client.post(reverse('like', args=[test_post_id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PostLike.objects.filter(owner=self.post).exists())
        response = self.client.post(reverse('like', args=[test_post_id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(PostLike.objects.filter(owner=self.post).exists())

    def test_add_comment(self):
        test_post_id = self.post.id
        self.assertFalse(Comment.objects.filter(post = self.post).count() > 1)
        response = self.client.post(reverse('add_comment', args=[test_post_id]), {'content': 'test comment'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Comment.objects.filter(post = self.post).count() > 1)

    def test_like_comment(self):
        self.assertFalse(CommentLike.objects.filter(owner=self.comment).exists())
        response = self.client.post(reverse('comment_like', args=[self.post.id]),)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CommentLike.objects.filter(owner=self.comment).exists())

    def test_unlike_comment(self):
        self.assertFalse(CommentLike.objects.filter(owner=self.comment).exists())
        response = self.client.post(reverse('comment_like', args=[self.post.id]), )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CommentLike.objects.filter(owner=self.comment).exists())
        response = self.client.post(reverse('comment_like', args=[self.post.id]), )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(CommentLike.objects.filter(owner=self.comment).exists())