from django.test import TestCase, Client
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from node.models import Author
import hashlib
import json

User = get_user_model()


class AuthorListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create 5 authors for testing
        number_of_authors = 5
        for author_num in range(number_of_authors):
            User.objects.create_user(
                id=author_num,
                display_name=f"Author {author_num}",
                host=f"host{author_num}.com",
                github=f"https://github.com/author{author_num}",
                profile_image=f"https://imagehost.com/author{author_num}.png",
                page=f"https://profile.com/author{author_num}",
                email=f"author{author_num}@example.com",
                password="password123"
            )

    def setUp(self):
        self.client = APIClient()
        self.author1 = User.objects.create_user(id=6, display_name="Test Author1", description="Test Description",
                                                github="torvalds", email="author1@test.com", password="pass")

    def login(self, author):
        # Signup new user
        # signup_data = {
        #     'display_name': 'Test User',
        #     'email': 'testuser@example.com',
        #     'password': 'password123',
        #     'confirm_password': 'password123',
        # }
        # response1 = self.client.post(
        #     reverse('api_signup'),
        #     data=json.dumps(signup_data),
        #     content_type='application/json',
        # )
        # self.assertEqual(response1.status_code, 200)

        # Now log in the newly created user
        login_data = {
            'email': author.email,
            'password': 'pass',
            'next': '/node/'  # Optional, based on your frontend
        }
        response = self.client.post(
            reverse('api_login'),
            data=json.dumps(login_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response

    def test_view_url_exists_at_desired_location(self):
        login = self.login()  # Ensure the user is signed up and logged in first
        if login.status_code == 200:
            response = self.client.get('/node/authors/')
            self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        login = self.login(self.author1)  # Ensure the user is signed up and logged in first\
        if login.status_code == 200:
            response = self.client.get(reverse('authors'))
            self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        login = self.login(self.author1)  # Ensure the user is signed up and logged in first
        if login.status_code == 200:
            response = self.client.get(reverse('authors'))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'authors.html')

    def test_all_authors_are_listed(self):
        login = self.login(self.author1)  # Ensure the user is signed up and logged in first
        if login.status_code == 200:
            response = self.client.get(reverse('authors'))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context['authors']), 6)

    def test_author_search_functionality(self):
        login = self.login(self.author1)  # Ensure the user is signed up and logged in first
        if login.status_code == 200:
            response = self.client.get(reverse('authors') + '?q=Author 1')
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Author 1")
            self.assertEqual(len(response.context['authors']), 1)