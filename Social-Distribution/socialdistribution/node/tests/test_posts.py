import datetime
import sys

from django.contrib.auth import login
from django.utils import timezone
from rest_framework.test import APIClient

sys.path.append('../node')

from http.client import responses

from django.core import signing
from django.urls import reverse

from node.models import Author, Post, Comment, PostLike, CommentLike, Follow, AuthorManager
from django.test import TestCase, Client
from node import views
from django.utils import timezone
import datetime


class PostTests(TestCase):

    def setUp(self):

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

        self.private_post = Post.objects.create(
            title="Private Title",
            description="Test Description",
            contentType="text/plain",
            text_content="Test Content",
            author=None,
            visibility="PRIVATE",
            published = timezone.make_aware(datetime.datetime.now(), datetime.timezone.utc),
        )

        self.comment = Comment.objects.create(
            author=self.author,
            post=self.post,
            text="Test Comment text"
        )

        self.friend_author = Author.objects.create(display_name="Test Friend",
                                                   email='friendAuthor@test.com'
                                                   )

        self.friends_post = Post.objects.create(
            title="Private Title",
            description="Test Description",
            contentType="text/plain",
            text_content="Test Content",
            author=self.friend_author,
            visibility="FRIENDS",
            published=timezone.make_aware(datetime.datetime.now(), datetime.timezone.utc),
        )

        self.client = APIClient()
        self.client.login(username="testAuthor", password="password")

        signed_id = signing.dumps(self.author.id)
        self.client.cookies['id'] = signed_id

    def tearDown(self):
        # Written with aid of Microsoft Copilot, Oct. 2024
        PostLike.objects.all().delete()
        Comment.objects.all().delete()
        Post.objects.all().delete()
        Author.objects.all().delete()
        self.client.cookies.clear()

    def test_post_creation(self):
            self.assertEqual(self.post.title, "Test Title")
            self.assertEqual(self.post.author.display_name, "Test Author")

    def test_add_post(self):
            response = self.client.get(reverse('add'), follow=True)
            self.assertEqual(response.status_code, 200)
            response = self.client.post(f'api/authors/{self.author.id}/posts', {'title': 'New Post',
                                                            'body-text': 'Test Description',
                                                            'visibility': 'PUBLIC',
                                                            'contentType': 'text/plain',
                                                            'content': 'Test Content',
                                                            'description': 'Test Description',
                                                            'author': self.author,
                                                              })
            self.assertEqual(response.status_code, 302)
            self.assertTrue(Post.objects.filter(title="New Post").exists())

    def test_like_post(self):
        test_post_id = self.post.id
        self.assertFalse(PostLike.objects.filter(owner=self.post).exists())
        response = self.client.post(reverse('like', args=[test_post_id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PostLike.objects.filter(owner=self.post).exists())

    def test_unlike_post(self):
        self.client.force_authenticate(user=self.author)
        test_post_id = self.post.id
        self.assertFalse(PostLike.objects.filter(owner=self.post).exists())
        response = self.client.post(reverse('like', args=[test_post_id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PostLike.objects.filter(owner=self.post).exists())
        response = self.client.post(reverse('like', args=[test_post_id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(PostLike.objects.filter(owner=self.post).exists())

    def test_add_comment(self):
        self.client.force_authenticate(user=self.author)
        test_post_id = self.post.id
        self.assertFalse(Comment.objects.filter(post = self.post).count() > 1)
        response = self.client.post(reverse('add_comment', args=[test_post_id]),
                                    {'content': 'test comment'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Comment.objects.filter(post = self.post).count() > 1)

    def test_like_comment(self):
        self.assertFalse(CommentLike.objects.filter(owner=self.comment).exists())
        response = self.client.post(reverse('comment_like'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CommentLike.objects.filter(owner=self.comment).exists())

    def test_unlike_comment(self):
        self.assertFalse(CommentLike.objects.filter(owner=self.comment).exists())
        response = self.client.post(reverse('comment_like'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CommentLike.objects.filter(owner=self.comment).exists())
        response = self.client.post(reverse('comment_like'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(CommentLike.objects.filter(owner=self.comment).exists())

    def test_private_post(self):
        response = self.client.get(reverse('view_post', args=[self.private_post.id]), follow=True)
        self.assertEqual(response.status_code, 403)

    def test_friends_post(self):
        response = self.client.get(reverse('view_post', args=[self.friends_post.id]), follow=True)
        self.assertEqual(response.status_code, 403)
        self.following_friend = Follow.objects.create(
            follower=self.author,
            following=self.friend_author)
        self.following_author = Follow.objects.create(
            follower=self.friend_author,
            following=self.author)
        response = self.client.get(reverse('view_post', args=[self.friends_post.id]), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_add_post_API_call(self):
        self.client.force_authenticate(user=self.author)
        url = f'http://localhost:8000/api/authors/{self.author.id}/posts'
        response = self.client.post(url, data={'title': 'API Title',
                                                       'description': 'Test Description',
                                                       'content': 'Test Content',
                                                       'contentType': 'text/plain',
                                                       'visibility': 'PUBLIC',
                                                       'author': self.author,})
        self.assertEqual(response.status_code, 303)
        self.assertTrue(Post.objects.filter(title="API Title").exists())