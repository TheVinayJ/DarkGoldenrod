from django.test import TestCase
from django.urls import reverse
from node.models import Author, Follow, Post
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
import hashlib
import json

User = get_user_model()


# With help from Chat-GPT 4o, OpenAI, 2024-10-19
class FeedTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create test authors
        cls.author1 = User.objects.create_user(
            display_name="Author 1",
            email="author1@example.com",
            password=hashlib.sha256("password123".encode()).hexdigest()
        )
        cls.author2 = User.objects.create_user(
            display_name="Author 2",
            email="author2@example.com",
            password=hashlib.sha256("password123".encode()).hexdigest()
        )
        cls.author3 = User.objects.create_user(
            display_name="Author 3",
            email="author3@example.com",
            password=hashlib.sha256("password123".encode()).hexdigest()
        )
        cls.author4 = User.objects.create_user(
            display_name="Author 4",
            email="author4@example.com",
            password=hashlib.sha256("password123".encode()).hexdigest()
        )

        # Create posts with different visibility and published dates
        now = datetime.now()
        Post.objects.create(author=cls.author2, text_content="Public post by Author 2", visibility="PUBLIC", published=now - timedelta(days=10))
        Post.objects.create(author=cls.author2, text_content="Unlisted post by Author 2", visibility="UNLISTED", published=now - timedelta(days=9))
        Post.objects.create(author=cls.author2, text_content="Friends-only post by Author 2", visibility="FRIENDS", published=now - timedelta(days=8))
        Post.objects.create(author=cls.author3, text_content="Public post by Author 3", visibility="PUBLIC", published=now - timedelta(days=7))
        Post.objects.create(author=cls.author3, text_content="Unlisted post by Author 3", visibility="UNLISTED", published=now - timedelta(days=6))
        Post.objects.create(author=cls.author3, text_content="Friends-only post by Author 3", visibility="FRIENDS", published=now - timedelta(days=5))
        Post.objects.create(author=cls.author4, text_content="Public post by Author 4", visibility="PUBLIC", published=now - timedelta(days=4))
        Post.objects.create(author=cls.author4, text_content="Unlisted post by Author 4", visibility="UNLISTED", published=now - timedelta(days=3))
        Post.objects.create(author=cls.author4, text_content="Friends-only post by Author 4", visibility="FRIENDS", published=now)
        

        # Set up following and mutual follow (friendship)
        Follow.objects.create(follower="http://darkgoldenrod/api/authors/" + str(cls.author1.id),
                              following="http://darkgoldenrod/api/authors/" + str(cls.author2.id),
                              approved=True)
        Follow.objects.create(follower="http://darkgoldenrod/api/authors/" + str(cls.author2.id),
                              following="http://darkgoldenrod/api/authors/" + str(cls.author1.id),
                              approved=True)  # Mutual follow
        Follow.objects.create(follower="http://darkgoldenrod/api/authors/" + str(cls.author3.id),
                              following="http://darkgoldenrod/api/authors/" + str(cls.author1.id),
                              approved=True)  # Author 3 follow Author 1
        Follow.objects.create(follower="http://darkgoldenrod/api/authors/" + str(cls.author1.id),
                              following="http://darkgoldenrod/api/authors/" + str(cls.author3.id),
                              approved=False)  # Author 1 don't follow Author 3
        Follow.objects.create(follower="http://darkgoldenrod/api/authors/" + str(cls.author1.id),
                              following="http://darkgoldenrod/api/authors/" + str(cls.author4.id),
                              approved=True)  # Author 1 follow Author 4

    # login function follows Duy Bui's login_user test
    def login(self, author):
        login_data = {
            'email': author.email,
            'password': hashlib.sha256("password123".encode()).hexdigest(),
            'next': '/node/'  # Optional, based on your frontend
        }
        response = self.client.post(
            reverse('api_login'),
            data=json.dumps(login_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        return response

    def test_all_filter(self):
        # Log in as author1
        login = self.login(self.author1)
        if login.status_code == 200:

            # Get the feed
            response = self.client.get(reverse('following_feed'))
            self.assertEqual(response.status_code, 200)

            # Check that the feed contains the expected posts:
            # 1. Public and Unlisted posts from followed authors (Author 2 & 4)
            self.assertContains(response, "Public post by Author 2")
            self.assertContains(response, "Unlisted post by Author 2")
            self.assertContains(response, "Friends-only post by Author 2")
            self.assertContains(response, "Public post by Author 4")
            self.assertContains(response, "Unlisted post by Author 4")

            # 3. Public posts from all authors
            self.assertContains(response, "Public post by Author 3")

            # Check that the feed does not contain posts that author1 should not see
            self.assertNotContains(response, "Unlisted post by Author 3")  # No unlisted post from non-followed or non-friends
            self.assertNotContains(response, "Friends-only post by Author 3")   # No friends post from non-followed or non-friends
            self.assertNotContains(response, "Friends-only post by Author 4")   # No friends post from non-friends

            # Check that posts are ordered from newest to oldest
            posts_in_order = [
                "Unlisted post by Author 4",
                "Public post by Author 4",
                "Public post by Author 3",
                "Friends-only post by Author 2",
                "Unlisted post by Author 2",
                "Public post by Author 2",
            ]
            content = response.content.decode("utf-8")
            for i in range(len(posts_in_order) - 1):
                self.assertLess(content.index(posts_in_order[i]), content.index(posts_in_order[i + 1]))


    def test_following_filter(self):
        login = self.login(self.author1)
        if login.status_code == 200:

            # Apply the "followings" filter
            response = self.client.get(reverse('following_feed') + '?filter=followings')
            self.assertEqual(response.status_code, 200)

            # Check that the feed contains the expected posts from followings (Author 2)
            self.assertContains(response, "Public post by Author 2")
            self.assertContains(response, "Unlisted post by Author 2")
            self.assertContains(response, "Friends-only post by Author 2")
            self.assertContains(response, "Public post by Author 4")
            self.assertContains(response, "Unlisted post by Author 4")

            # Ensure posts from non-followed authors do not appear
            self.assertNotContains(response, "Public post by Author 3")
            self.assertNotContains(response, "Unlisted post by Author 3")  # No unlisted post from non-followed or non-friends
            self.assertNotContains(response, "Friends-only post by Author 3")   # No friends post from non-followed or non-friends
            self.assertNotContains(response, "Friends-only post by Author 4")   # No friends post from non-friends

            # Check that posts are ordered from newest to oldest
            posts_in_order = [
                "Unlisted post by Author 4",
                "Public post by Author 4",
                "Friends-only post by Author 2",
                "Unlisted post by Author 2",
                "Public post by Author 2",
            ]
            content = response.content.decode("utf-8")
            for i in range(len(posts_in_order) - 1):
                self.assertLess(content.index(posts_in_order[i]), content.index(posts_in_order[i + 1]))

    def test_friends_filter(self):
        login = self.login(self.author1)
        if login.status_code == 200:

            # Apply the "friends" filter
            response = self.client.get(reverse('following_feed') + '?filter=friends')
            self.assertEqual(response.status_code, 200)

            # Check that the feed contains posts from friends (mutual follow with Author 2)
            self.assertContains(response, "Public post by Author 2")
            self.assertContains(response, "Unlisted post by Author 2")
            self.assertContains(response, "Friends-only post by Author 2")

            # Ensure posts from non-friends do not appear
            self.assertNotContains(response, "Public post by Author 3")
            self.assertNotContains(response, "Unlisted post by Author 3")  # No unlisted post from non-followed or non-friends
            self.assertNotContains(response, "Friends-only post by Author 3")   # No friends post from non-followed or non-friends
            self.assertNotContains(response, "Public post by Author 4")
            self.assertNotContains(response, "Unlisted post by Author 4")  # No unlisted post from non-friends
            self.assertNotContains(response, "Friends-only post by Author 4")   # No friends post from non-friends

            # Check that posts are ordered from newest to oldest
            posts_in_order = [
                "Unlisted post by Author 2",
                "Public post by Author 2",
            ]
            content = response.content.decode("utf-8")
            for i in range(len(posts_in_order) - 1):
                self.assertLess(content.index(posts_in_order[i]), content.index(posts_in_order[i + 1]))


    def test_reposts_filter(self):
        # Log in as author1
        login = self.login(self.author1)
        if login.status_code == 200:
            # Apply the "reposts" filter
            response = self.client.get(reverse('following_feed') + '?filter=reposts')
            self.assertEqual(response.status_code, 200)

            # Check that the feed contains reposts (Add repost creation logic in setup if needed)
            # Example: self.assertContains(response, "Repost of: Original post by Author 2")

            # Ensure original posts do not appear
            self.assertNotContains(response, "Public post by Author 2")
            self.assertNotContains(response, "Public post by Author 3")

