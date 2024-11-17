import json
import sys

sys.path.append('../node')

from django.urls import reverse
from django.utils import timezone
from node.models import Post, Follow, Comment, PostLike, CommentLike
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from node.views import retrieve_github
import datetime

User = get_user_model()

# Create your tests here.
class ProfileTests(TestCase):
    def setUp(self):
        self.author1 = User.objects.create_user(id=1, display_name="Test Author1", description="Test Description", github="torvalds", email="author1@test.com", password="pass")
        self.author2 = User.objects.create_user(id=2, display_name="Test Author2", email="author2@test.com", password="pass")
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
        self.client.cookies.clear()

    # login function follows Duy Bui's test_login_success test
    def login(self, author):
        login_data = {
            'email': author.email,
            'password': "pass",
            'next': '/node/'  # Optional, based on your frontend
        }
        response = self.client.post(
            reverse('api_login'),
            data=json.dumps(login_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
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

    def test_ui_post_order_display(self):
        login = self.login(self.author1)
        if login.status_code == 200:

            response = self.client.get(reverse('profile', args=[self.author1.id]))
            posts = response.context['posts']
            # make sure most recent posts first
            self.assertEqual(posts[0], self.post3)  # recent post, last created in setUp
            self.assertEqual(posts[1], self.post2)  # older post

    def test_friend_post_visibility_on_profile(self):
        login = self.login(self.author2)
        if login.status_code == 200:
            response = self.client.get(
                reverse('profile', args=[self.author1.id]))  # viewing their author1(who does not follow back) profile
            posts = response.context['posts']
            self.assertNotIn(self.post3, posts)

    def test_api_successful_edit_profile(self):
        login = self.login(self.author1)
        if login.status_code == 200:
            url = f'/api/authors/{self.author1.id}/'
            edit_changes = {"display_name": "New Display Name",
                            "description": "New Description",
                            }
            response = self.client.put(url, edit_changes, content_type='application/json')
            self.assertEqual(response.status_code, 200)

            self.author1.refresh_from_db()
            self.assertEqual(self.author1.display_name, 'New Display Name')
            self.assertEqual(self.author1.description, 'New Description')

    def test_api_successful_update_github_edit_profile(self):
        login = self.login(self.author1)
        if login.status_code == 200:
            url = f'/api/authors/{self.author1.id}/'
            edit_changes = {"display_name": "Test Author1",
                            "github": "tianah703"
                            }
            response = self.client.put(url, edit_changes, content_type='application/json')
            self.assertEqual(response.status_code, 200)

            self.author1.refresh_from_db()
            self.assertEqual(self.author1.github, "tianah703")
            retrieve_github(self.author1)

            posts = Post.objects.filter(author=self.author1, description="Public Github Activity")
            for post in posts:
                self.assertIn("tianah703", post.text_content)


    def test_api_successful_remove_github_edit_profile(self):
        login = self.login(self.author1)
        if login.status_code == 200:
            url = f'/api/authors/{self.author1.id}/'
            edit_changes = {"display_name": "Test Author1",
                            "github": ""
                            }
            response = self.client.put(url, edit_changes, content_type='application/json')
            self.assertEqual(response.status_code, 200)

            self.author1.refresh_from_db()
            self.assertEqual(Post.objects.filter(author=self.author1, description="Public Github Activity").count(), 0)

    def test_api_unsuccessful_edit_profile(self):
        login = self.login(self.author1)
        if login.status_code == 200:
            url = f'/api/authors/{self.author1.id}/'
            edit_changes = {"display_name": "",
                            "profile_image": None,
                            "description": "i want a blank display name",
                            "github": ""
                            }
            response = self.client.put(url, edit_changes, content_type='application/json')
            self.assertEqual(response.status_code, 400)

    def test_api_retrieval_profile(self):
        login = self.login(self.author1)
        if login.status_code == 200:
            url = f'/api/authors/{self.author1.id}/'
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            expected_data = {
                "type": "author",
                "id": f"http://darkgoldenrod/api/authors/{self.author1.id}",
                "host": "http://darkgoldenrod/api/",
                "displayName": "Test Author1",
                "github": "http://github.com/torvalds",
                "profileImage": None,
                "page": f"http://darkgoldenrod/authors/{self.author1.id}/profile",
            }

            response_data = response.json()

            self.assertEqual(response_data['type'], expected_data['type'])
            self.assertEqual(response_data['id'], expected_data['id'])
            self.assertEqual(response_data['host'], expected_data['host'])
            self.assertEqual(response_data['displayName'], expected_data['displayName'])
            self.assertEqual(response_data['github'], expected_data['github'])
            self.assertEqual(response_data['profileImage'], expected_data['profileImage'])
            self.assertEqual(response_data['page'], expected_data['page'])

    def test_api_retrieval_nonexistent_profile(self):
        login = self.login(self.author1)
        if login.status_code == 200:
            url = f'/api/authors/3/'
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)