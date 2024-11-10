import sys

sys.path.append('../node')

from django.test import TestCase, Client
from django.urls import reverse
from django.core import signing
from http.client import responses

from django.core import signing
from django.urls import reverse
from django.utils import timezone
from node.models import Author, Post, Follow, Comment, PostLike, CommentLike
from django.test import TestCase, Client
from node import views
import datetime

# Create your tests here.
class ProfileTests(TestCase):
    def setUp(self):
        self.author1 = Author.objects.create(id=1, display_name="Test Author1", description="Test Description", github="torvalds", email='author1@test.com')
        self.author2 = Author.objects.create(id=2, display_name="Test Author2", email='author2@test.com')
        # author 2 is following author 1 (but is not followed back)
        self.follow1 = Follow.objects.create(follower="http://darkgoldenrod/api/authors/"+ str(self.author2.id),
                                             following="http://darkgoldenrod/api/authors/"+ str(self.author1.id))

        # cannot customize published date due to auto_now_add=True
        self.post1 = Post.objects.create(
            id = 1,
            title="Post 1",
            description="Description 1",
            text_content="Content 1",
            author=self.author1,
            published=timezone.make_aware(datetime.datetime.now(), datetime.timezone.utc),
            visibility="PUBLIC"
        )
        self.post2 = Post.objects.create(
            title="Post 2",
            description="Description 2",
            text_content="Content 2",
            author=self.author1,
            published=timezone.make_aware(datetime.datetime.now(), datetime.timezone.utc),
            visibility="PUBLIC"
        )

        self.post3 = Post.objects.create(
            title="Post 3",
            description="Happy New Millennium",
            text_content="Content 3",
            author=self.author1,
            published=timezone.make_aware(datetime.datetime.now(), datetime.timezone.utc),
            visibility="FRIENDS" # friends only post
        )

        self.client = Client()

    def tearDown(self):
        # Written with aid of Microsoft Copilot, Oct. 2024
        PostLike.objects.all().delete()
        Comment.objects.all().delete()
        Post.objects.all().delete()
        Author.objects.all().delete()
        self.client.cookies.clear()

    # login function follows Duy Bui's login_user test
    def login(self, author):
        login_data = {
            'email': author.email,
            'password': author.password,
            'next': '/node/'  # Optional, based on your frontend
        }
        response = self.client.post(
            reverse('api_login'),
            data=login_data,  # Pass as dict; APIClient handles serialization
            format='json'  # Automatically serializes to JSON
        )
        return response

    def test_author_content(self):
        login = self.login(self.author1)
        if login.status_code == 200:
            response = self.client.get(reverse('profile', args=[self.author1.id]))
            # make sure author's info displayed correct
            self.assertContains(response, "Test Author1")  # Check display name
            self.assertContains(response, "Test Description")  # Check description
            self.assertEqual(response.status_code, 200)

    def test_ui_github_activity_display(self):
        login = self.login(self.author1)
        if login.status_code == 200:
            response = self.client.get(reverse('profile', args=[self.author1.id]))
            self.assertTrue(response.context['activity']) # make sure GitHub section not empty

    def test_edit_profile(self):
        login = self.login(self.author1)
        if login.status_code == 200:

            new_data = {
                'display_name': 'Updated Author',
                'description': 'Updated Description',
            }
            response = self.client.post(reverse('profile_edit', args=[self.author1.id]), new_data)
            self.author1.refresh_from_db()
            self.assertEqual(self.author1.display_name, 'Updated Author')
            self.assertEqual(self.author1.description, 'Updated Description')
            self.assertRedirects(response, reverse('profile', args=[self.author1.id])) # check if redirect properly
            self.assertEqual(response.status_code, 302) # new edited data successfully moved

    def test_ui_post_order_display(self):
        login = self.login(self.author1)
        if login.status_code == 200:

            response = self.client.get(reverse('profile', args=[self.author1.id]))
            posts = response.context['posts']
            # make sure most recent posts first
            self.assertEqual(posts[0], self.post3)  # recent post, last created in setUp
            self.assertEqual(posts[1], self.post2)  # older post

    def test_friend_post_visibility(self):
        login = self.login(self.author1)
        if login.status_code == 200:

            response = self.client.get(
                reverse('profile', args=[self.author1.id]))  # viewing their author1(who does not follow back) profile
            posts = response.context['posts']
            self.assertNotIn(self.post3, posts)

class EditPostTests(TestCase):
    def setUp(self):
        self.author1 = Author.objects.create(id=1, display_name="Test Author1", description="Test Description", github='torvalds', email='author3@test.com')
        self.author2 = Author.objects.create(id=2, display_name="Test Author2", email='author4@test.com')

        # cannot customize published date due to auto_now_add=True
        self.post1 = Post.objects.create(
            id = 1,
            title="Post 1",
            description="Description 1",
            text_content="Content 1",
            author=self.author1,
            published=timezone.make_aware(datetime.datetime.now(), datetime.timezone.utc),
            visibility="PUBLIC")

    def tearDown(self):
        # Written with aid of Microsoft Copilot, Oct. 2024
        PostLike.objects.all().delete()
        Comment.objects.all().delete()
        Post.objects.all().delete()
        Author.objects.all().delete()
        self.client.cookies.clear()

    def test_other_authors_cannot_modify(self):
        # login function follows Duy Bui's login_user test
        login_data = {
            'email': self.author1.email,
            'password': self.author1.password,
            'next': '/node/'  # Optional, based on your frontend
        }
        response = self.client.post(
            reverse('api_login'),
            data=login_data,  # Pass as dict; APIClient handles serialization
            format='json'  # Automatically serializes to JSON
        )
        if response.status_code == 200:
            response = self.client.get(reverse('view_post', args=[self.post1.id]))
            self.assertNotContains(response, 'Edit Post')
