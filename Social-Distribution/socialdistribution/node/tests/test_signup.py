from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from django.test import override_settings
import json

# The tests in this file and the helper function was written and debugged with OpenAI, ChatGPT o1-mini

User = get_user_model()

class APISignupViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.signup_url = reverse('api_signup')

    def test_signup_success(self):
        """
        Ensure we can create a new user with valid data.
        """
        with override_settings(SECURE_SSL_REDIRECT=False):
            data = {
                'email': 'testuser@example.com',
                'display_name': 'Test User',
                'password': 'testpassword123',
                'confirm_password': 'testpassword123',
            }

            response = self.client.post(
                self.signup_url,
                data,
                format='json'
            )

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            response_data = response.json()

            # Check response content
            self.assertIn('message', response_data)
            self.assertEqual(response_data['message'], 'Signup successful')
            self.assertIn('next', response_data)
            self.assertEqual(response_data['next'], '/node/')
            self.assertIn('user_id', response_data)

            # Verify that the user was created in the database
            self.assertTrue(User.objects.filter(email='testuser@example.com').exists())

    def test_signup_existing_email(self):
        """
        Ensure that signing up with an existing email returns an error.
        """
        with override_settings(SECURE_SSL_REDIRECT=False):
            User.objects.create_user(
                email='existing@example.com',
                password='password123',
                display_name='Existing User'
            )
            data = {
                'email': 'existing@example.com',
                'display_name': 'Test User',
                'password': 'testpassword123',
                'confirm_password': 'testpassword123',
                'next': '/node/'
            }
            response = self.client.post(
                self.signup_url,
                data=json.dumps(data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 400)

            response_data = response.json()

            self.assertIn('email', response_data)
            self.assertEqual(response_data['email'], ['author with this email already exists.'])

    def test_signup_invalid_email(self):
        """
        Ensure that signing up with an invalid email returns an error.
        """
        with override_settings(SECURE_SSL_REDIRECT=False):
            data = {
                'email': 'invalidemail',
                'display_name': 'Test User',
                'password': 'testpassword123',
                'confirm_password': 'testpassword123',
                'next': '/node/'
            }
            response = self.client.post(
                self.signup_url,
                data=json.dumps(data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 400)

            # Parse JSON response
            response_data = response.json()

            # Check error message
            self.assertIn('email', response_data)
            self.assertEqual(response_data['email'], ['Enter a valid email address.'])

    def test_signup_missing_fields(self):
        """
        Ensure that signing up with missing fields returns errors.
        """
        with override_settings(SECURE_SSL_REDIRECT=False):
            data = {
                'email': '',
                'display_name': '',
                'password': '',
                'confirm_password': '',
                'next': '/node/'
            }
            response = self.client.post(
                self.signup_url,
                data=json.dumps(data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 400)

            # Parse JSON response
            response_data = response.json()

            # Check error messages for each field
            expected_errors = {
                'email': ['This field may not be blank.'],
                'password': ['This field may not be blank.'],
                'confirm_password': ['This field may not be blank.'],
            }
            self.assertEqual(response_data, expected_errors)

    def test_signup_password_mismatch(self):
        """
        Ensure that signing up with mismatched passwords returns an error.
        """
        with override_settings(SECURE_SSL_REDIRECT=False):
            data = {
                'email': 'testuser@example.com',
                'display_name': 'Test User',
                'password': 'password123',
                'confirm_password': 'differentpassword',
                'next': '/node/'
            }
            response = self.client.post(
                self.signup_url,
                data=json.dumps(data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 400)

            # Parse JSON response
            response_data = response.json()

            # Check error message
            self.assertIn('password', response_data)
            self.assertEqual(response_data['password'], ['Passwords must match.'])

    def test_signup_success_sets_cookies(self):
        """
        Ensure that signup sets the access_token and user_id cookies.
        """
        with override_settings(SECURE_SSL_REDIRECT=False):
            data = {
                'email': 'testuser@example.com',
                'display_name': 'Test User',
                'password': 'testpassword123',
                'confirm_password': 'testpassword123',
                'next': '/node/'
            }
            response = self.client.post(
                self.signup_url,
                data=json.dumps(data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 201)

            # Check for access_token and user_id cookies
            self.assertIn('access_token', response.cookies)
            self.assertIn('user_id', response.cookies)
            self.assertEqual(response.cookies['user_id'].value, str(response.json()['user_id']))