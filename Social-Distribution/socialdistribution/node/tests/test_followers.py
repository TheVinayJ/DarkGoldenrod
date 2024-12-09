from django.test import TestCase, override_settings
from django.urls import reverse
from node.models import Author, Follow
import hashlib

class AuthorFollowerTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create two authors for testing follow and unfollow functionality
        cls.author1 = Author.objects.create(
            id="1ce5e487-085c-4e8e-8c46-7b9045837821",
            display_name="Author 1",
            email="author1@example.com",
            password=hashlib.sha256("password123".encode()).hexdigest()
        )
        cls.author2 = Author.objects.create(
            id="1ce5e487-085c-4e8e-8c46-7b9045837822",
            display_name="Author 2",
            email="author2@example.com",
            password=hashlib.sha256("password123".encode()).hexdigest()
        )
        cls.author3 = Author.objects.create(
            id="1ce5e487-085c-4e8e-8c46-7b9045837823",
            display_name="Author 3",
            email="author3@example.com",
            password=hashlib.sha256("password123".encode()).hexdigest()
        )
        cls.author4 = Author.objects.create(
            id="1ce5e487-085c-4e8e-8c46-7b9045837824",
            display_name="Author 4",
            email="author4@example.com",
            password=hashlib.sha256("password123".encode()).hexdigest()
        )
        # Create another Follow object where author1 follows author2
        cls.follow1 = Follow.objects.create(
            follower=cls.author1.host + "/authors/" + str(cls.author1.id),
            following=cls.author2.host + "/authors/" + str(cls.author2.id),
            approved=True  # This could represent a follow request not yet approved
        )
        # Create another Follow object where author3 follows author2
        cls.follow2 = Follow.objects.create(
            follower=cls.author3.host + "/authors/" + str(cls.author3.id),
            following=cls.author2.host + "/authors/" + str(cls.author2.id),
            approved=False  # This could represent a follow request not yet approved
        )
        cls.follow3 = Follow.objects.create(
            follower=cls.author4.host + "/authors/" + str(cls.author4.id),
            following=cls.author2.host + "/authors/" + str(cls.author2.id),
            approved=True  # This could represent a follow request not yet approved
        )
        

    # login function follows Duy Bui's login_user test
    def login(self, author):
        with override_settings(SECURE_SSL_REDIRECT=False):
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

    def test_list_follower(self):
        login = self.login(self.author1)
        self.assertEqual(login.status_code, 200)
        if login.status_code == 200:

            # Test listing all followers
            response = self.client.get(reverse('list_all_followers', args=["1ce5e487-085c-4e8e-8c46-7b9045837822"]))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Author 1')
            self.assertContains(response, 'Author 4')
            self.assertNotContains(response, 'Author 3')

    def test_list_followers(self):
        login = self.login(self.author1)
        self.assertEqual(login.status_code, 200)
        if login.status_code == 200:

            # Test listing all followers
            response = self.client.get(reverse('list_follower', args=["1ce5e487-085c-4e8e-8c46-7b9045837822", r'http%3A%2F%2Fdarkgoldenrod%2Fapi%2Fauthors%2F1']))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Author 1')
            self.assertNotContains(response, 'Author 3')
            self.assertNotContains(response, 'Author 4')