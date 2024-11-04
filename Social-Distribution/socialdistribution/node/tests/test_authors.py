from django.test import TestCase
from django.urls import reverse
from node.models import Author
import hashlib



class AuthorListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create 5 authors for testing
        number_of_authors = 5
        for author_num in range(number_of_authors):
            Author.objects.create(
                display_name=f"Author {author_num}",
                host=f"host{author_num}.com",
                github=f"https://github.com/author{author_num}",
                profile_image=f"https://imagehost.com/author{author_num}.png",
                page=f"https://profile.com/author{author_num}",
                email=f"author{author_num}@example.com",
                password=hashlib.sha256("password123".encode()).hexdigest()
            )

    def signup_and_login(self):
        # Signup new user
        signup_data = {
            'display_name': 'Test User',
            'email': 'testuser@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
        }
        self.client.post(reverse('signup'), signup_data)

        # Now log in the newly created user
        login_data = {
            'email': signup_data['email'],
            'password': signup_data['password'],
            'next': '/node/'  # Optional, based on your frontend
        }
        response = self.client.post(
            reverse('api_login'),
            data=login_data,  # Pass as dict; APIClient handles serialization
            format='json'  # Automatically serializes to JSON
        )
        return response
        self.assertEqual(response.status_code, 302)  # Should redirect to index on successful login

    def test_view_url_exists_at_desired_location(self):
        self.signup_and_login()  # Ensure the user is signed up and logged in first
        response = self.client.get('/node/authors/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        self.signup_and_login()  # Ensure the user is signed up and logged in first
        response = self.client.get(reverse('authors'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        self.signup_and_login()  # Ensure the user is signed up and logged in first
        response = self.client.get(reverse('authors'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authors.html')

    def test_all_authors_are_listed(self):
        self.signup_and_login()  # Ensure the user is signed up and logged in first
        response = self.client.get(reverse('authors'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['authors']), 6)

    def test_author_search_functionality(self):
        self.signup_and_login()  # Ensure the user is signed up and logged in first
        response = self.client.get(reverse('authors') + '?q=Author 1')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Author 1")
        self.assertEqual(len(response.context['authors']), 1)
