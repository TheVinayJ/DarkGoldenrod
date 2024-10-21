from django.test import TestCase
from django.urls import reverse
from node.models import Author, Follow
import hashlib

class AuthorFollowTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create two authors for testing follow and unfollow functionality
        cls.author1 = Author.objects.create(
            display_name="Author 1",
            email="author1@example.com",
            password=hashlib.sha256("password123".encode()).hexdigest()
        )
        cls.author2 = Author.objects.create(
            display_name="Author 2",
            email="author2@example.com",
            password=hashlib.sha256("password123".encode()).hexdigest()
        )

    def login(self, author):
        # Helper method to log in an author
        login_data = {
            'email': author.email,
            'password': 'password123',
        }
        response = self.client.post(reverse('login'), login_data)
        self.assertEqual(response.status_code, 302)  # Should redirect to index on successful login

    def test_follow_author(self):
        # Log in author1
        self.login(self.author1)

        # Author1 follows Author2
        response = self.client.post(reverse('follow_author', kwargs={'author_id': self.author2.id}))
        self.assertEqual(response.status_code, 302)  # Should redirect on successful follow

        # Check that a Follow object is created
        follow_exists = Follow.objects.filter(
            follower="http://darkgoldenrod/api/authors/" + str(self.author1.id),
            following="http://darkgoldenrod/api/authors/" + str(self.author2.id)
        ).exists()
        self.assertTrue(follow_exists)  # Follow relationship should exist

    def test_unfollow_author(self):
        # Log in author1
        self.login(self.author1)

        # Manually create a follow relationship
        Follow.objects.create(
            follower="http://darkgoldenrod/api/authors/" + str(self.author1.id),
            following="http://darkgoldenrod/api/authors/" + str(self.author2.id)
        )

        # Author1 unfollows Author2
        response = self.client.post(reverse('unfollow_author', kwargs={'author_id': self.author2.id}))
        self.assertEqual(response.status_code, 302)  # Should redirect on successful unfollow

        # Check that the follow relationship is deleted
        follow_exists = Follow.objects.filter(
            follower="http://darkgoldenrod/api/authors/" + str(self.author1.id),
            following="http://darkgoldenrod/api/authors/" + str(self.author2.id)
        ).exists()
        self.assertFalse(follow_exists)  # Follow relationship should no longer exist

    def test_ui_follow_button_display(self):
        # Log in author1
        self.login(self.author1)

        # Check if follow button appears when author1 is not following author2
        response = self.client.get(reverse('authors'))
        self.assertContains(response, 'Follow')  # Should contain follow button text

        # Now follow author2
        Follow.objects.create(
            follower="http://darkgoldenrod/api/authors/" + str(self.author1.id),
            following="http://darkgoldenrod/api/authors/" + str(self.author2.id)
        )

        # Check if unfollow button appears when author1 is following author2
        response = self.client.get(reverse('authors'))
        self.assertContains(response, 'Unfollow')  # Should contain unfollow button text
