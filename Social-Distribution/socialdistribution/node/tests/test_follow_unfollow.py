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

    def test_follow_author(self):
        login = self.login(self.author1)
        self.assertEqual(login.status_code, 200)
        if login.status_code == 200:

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
        login = self.login(self.author1)
        self.assertEqual(login.status_code, 200)
        if login.status_code == 200:

            # Manually create a follow relationship
            Follow.objects.create(
                follower="http://darkgoldenrod/api/authors/" + str(self.author1.id),
                following="http://darkgoldenrod/api/authors/" + str(self.author2.id),
                approved = True,
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
        login = self.login(self.author1)
        if login.status_code == 200:

            # Check if follow button appears when author1 is not following author2
            response = self.client.get(reverse('authors'))
            self.assertContains(response, 'Follow')  # Should contain follow button text

            # Now follow author2
            Follow.objects.create(
                follower="http://darkgoldenrod/api/authors/" + str(self.author1.id),
                following="http://darkgoldenrod/api/authors/" + str(self.author2.id),
                approved=True,
            )

            # Check if unfollow button appears when author1 is following author2
            response = self.client.get(reverse('authors'))
            self.assertContains(response, 'Unfollow')  # Should contain unfollow button text

    def test_ui_friends_display(self):
        '''
        Whenever there is a friends relationship (authors follow each other back), test it is shown on both parties's friend page
        '''
        login = self.login(self.author1)
        if login.status_code == 200:
            # Manually create a friend relationship
            Follow.objects.create(
                follower="http://darkgoldenrod/api/authors/" + str(self.author1.id),
                following="http://darkgoldenrod/api/authors/" + str(self.author2.id),
                approved=True,
            )
            Follow.objects.create(
                follower="http://darkgoldenrod/api/authors/" + str(self.author2.id),
                following="http://darkgoldenrod/api/authors/" + str(self.author1.id),
                approved=True,
            )

            response1 = self.client.get(reverse('friends', args=[self.author1.id]))
            self.assertContains(response1, self.author2.display_name)
            response2 = self.client.get(reverse('friends', args=[self.author2.id]))
            self.assertContains(response2, self.author1.display_name)

    def test_ui_follow_relationship_display(self):
        '''
        Whenever there is a following relationship, test it is shown properly on both parties' followers/following page
        '''
        login = self.login(self.author1)
        if login.status_code == 200:
            # Manually create a friend relationship
            Follow.objects.create(
                follower="http://darkgoldenrod/api/authors/" + str(self.author1.id),
                following="http://darkgoldenrod/api/authors/" + str(self.author2.id),
                approved=True,
            )

            # author2 appears on author1's followings page
            response1 = self.client.get(reverse('following', args=[self.author1.id]))
            self.assertContains(response1, self.author2.display_name)
            # author1 appears on author2's followers page
            response2 = self.client.get(reverse('followers', args=[self.author2.id]))
            self.assertContains(response2, self.author1.display_name)

    def test_ui_follower_request_display(self):
        '''
        Whenever there is a follower request, test it is shown properly on the author's follower requests page
        '''
        login = self.login(self.author1)
        if login.status_code == 200:
            # Manually create a follower request
            Follow.objects.create(
                follower="http://darkgoldenrod/api/authors/" + str(self.author1.id),
                following="http://darkgoldenrod/api/authors/" + str(self.author2.id),
                approved=False,
            )

            response = self.client.get(reverse('follow_requests', args=[self.author1.id]))
            self.assertContains(response, self.author2.display_name)

    def test_reject_follower_request(self):
        '''
        Whenever there is a rejected follower request, it is deleted
        '''
        login = self.login(self.author1)
        if login.status_code == 200:
            # Manually create a follower request
            Follow.objects.create(
                follower="http://darkgoldenrod/api/authors/" + str(self.author1.id),
                following="http://darkgoldenrod/api/authors/" + str(self.author2.id),
                approved=False,
            )

            self.client.post(reverse('decline_follow', args=[self.author2.id, self.author1.id]))
            follow_exists = Follow.objects.filter(
                follower="http://darkgoldenrod/api/authors/" + str(self.author1.id),
                following="http://darkgoldenrod/api/authors/" + str(self.author2.id),
                approved=False,
            ).exists()
            self.assertFalse(follow_exists)

    def test_approve_follower_request(self):
        '''
        Whenever there is an approved follower request, the relationship is established
        '''
        login = self.login(self.author1)
        if login.status_code == 200:
            # Manually create a follower request
            Follow.objects.create(
                follower="http://darkgoldenrod/api/authors/" + str(self.author1.id),
                following="http://darkgoldenrod/api/authors/" + str(self.author2.id),
                approved=False,
            )

            self.client.post(reverse('approve_follow', args=[self.author2.id, self.author1.id]))
            follow_exists = Follow.objects.filter(
                follower="http://darkgoldenrod/api/authors/" + str(self.author1.id),
                following="http://darkgoldenrod/api/authors/" + str(self.author2.id),
                approved=True,
            ).exists()
            self.assertTrue(follow_exists)