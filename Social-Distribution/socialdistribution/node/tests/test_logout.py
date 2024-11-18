from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from django.test import override_settings, modify_settings
import json

# The tests in this file and the helper function was written and debugged with OpenAI, ChatGPT o1-mini

User = get_user_model()

class LogoutViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('api_login') 
        self.logout_url = reverse('api_logout')

        # Create a user for testing login and logout
        self.test_user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword123',
            display_name='Test User'
        )

    def login_user(self):
        """
        Helper method to log in the user and set the necessary authentication credentials.
        """
        login_data = {
            'email': 'testuser@example.com',
            'password': 'testpassword123',
            'next': '/node/'
        }
        response = self.client.post(
            self.login_url,
            data=login_data,
            format='json'
        )
        return response

    def test_logout_success(self):
        """
        Ensure that an authenticated user can successfully log out.
        """
        # First, log in the user to set the authentication credentials
        login_response = self.login_user()
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', login_response.cookies)
        self.assertIn('user_id', login_response.cookies)

        # Now, perform logout
        logout_response = self.client.post(
            self.logout_url,
            data={},
            format='json'
        )
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        # print(logout_response)
        # Parse JSON response
        response_data = logout_response.json()

        # Check response content
        self.assertIn('message', response_data)
        self.assertEqual(response_data['message'], 'Successfully logged out.')

        # Verify that the cookies are deleted (set to empty strings)
        self.assertIn('access_token', logout_response.cookies)
        self.assertEqual(logout_response.cookies['access_token'].value, '')
        self.assertIn('user_id', logout_response.cookies)
        self.assertEqual(logout_response.cookies['user_id'].value, '')