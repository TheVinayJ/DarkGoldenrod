from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from rest_framework_simplejwt.tokens import AccessToken
import json

User = get_user_model()

class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('api_login')

        # Create a user for testing login
        self.test_user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword123',
            display_name='Test User'
        )

    def test_login_success(self):
        """
        Ensure that a user can log in with valid credentials.
        """
        data = {
            'email': 'testuser@example.com',
            'password': 'testpassword123',
            'next': '/node/'
        }
        response = self.client.post(
            self.login_url,
            data=json.dumps(data),  
            content_type='application/json'  
        )
        self.assertEqual(response.status_code, 200)  # HTTP 200 OK

        # Parse JSON response
        response_data = response.json()

        # Check response content
        self.assertIn('message', response_data)
        self.assertEqual(response_data['message'], 'Login successful')
        self.assertIn('next', response_data)
        self.assertEqual(response_data['next'], '/node/')
        self.assertIn('user_id', response_data)
        self.assertEqual(response_data['user_id'], self.test_user.id)

        # Verify that the appropriate cookies are set
        self.assertIn('access_token', response.cookies)
        self.assertIn('user_id', response.cookies)
        self.assertEqual(response.cookies['user_id'].value, str(self.test_user.id))

    def test_login_non_existing_email(self):
        """
        Ensure that logging in with a non-existing email returns an error.
        """
        data = {
            'email': 'nonexistent@example.com',
            'password': 'somepassword',
            'next': '/node/'
        }
        response = self.client.post(
            self.login_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)  # HTTP 400 BAD REQUEST

        # Parse JSON response
        response_data = response.json()

        # Check error message
        self.assertEqual(response_data['non_field_errors'], ['Invalid email or password.'])

    def test_login_incorrect_password(self):
        """
        Ensure that logging in with an incorrect password returns an error.
        """
        data = {
            'email': 'testuser@example.com',
            'password': 'wrongpassword',
            'next': '/node/'
        }
        response = self.client.post(
            self.login_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)  # HTTP 400 BAD REQUEST

        # Parse JSON response
        response_data = response.json()

        # Check error message
        self.assertEqual(response_data['non_field_errors'], ['Invalid email or password.'])

    def test_login_missing_fields(self):
        """
        Ensure that logging in with missing fields returns errors.
        """
        data = {
            'email': '',
            'password': '',
            'next': '/node/'
        }
        response = self.client.post(
            self.login_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)  # HTTP 400 BAD REQUEST

        # Parse JSON response
        response_data = response.json()

        # Check error messages for each field
        expected_errors = {
            'email': ['This field may not be blank.'],
            'password': ['This field may not be blank.'],
        }
        
        self.assertEqual(response_data, expected_errors)

    def test_login_success_sets_cookies(self):
        """
        Ensure that successful login sets the access_token and user_id cookies.
        """
        data = {
            'email': 'testuser@example.com',
            'password': 'testpassword123',
            'next': '/node/'
        }
        response = self.client.post(
            self.login_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)  # HTTP 200 OK

        # Verify that the cookies are set
        self.assertIn('access_token', response.cookies)
        self.assertIn('user_id', response.cookies)
        self.assertEqual(response.cookies['user_id'].value, str(self.test_user.id))