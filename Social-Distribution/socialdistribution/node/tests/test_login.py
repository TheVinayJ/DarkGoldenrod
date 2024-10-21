from django.test import TestCase, Client
from django.urls import reverse
from django.core import signing
from node.models import Author
import hashlib

class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.index_url = reverse('index')
        self.password = 'password123'
        self.hashed_password = hashlib.sha256(self.password.encode()).hexdigest()
        self.author = Author.objects.create(
            display_name='Test User',
            email='testuser@example.com',
            password=self.hashed_password
        )

    #   The test sends a POST request to log in with correct credentials.
	#   It verifies that the user is redirected to the index page upon successful login.
	#   It retrieves the signed user ID from the login cookie.
	#   It decodes the signed cookie to get the actual user ID.
	#   It checks that the user ID from the cookie matches the logged-in user’s ID.
    #   Purpose: This test ensures that a user can successfully log in with the correct credentials.
    def test_login_success(self):
        """Test that a user can log in with correct credentials."""
        response = self.client.post(self.login_url, {
            'email': self.author.email,
            'password': self.password
        })
        self.assertRedirects(response, self.index_url)
        signed_id = self.client.cookies.get('id').value
        user_id = signing.loads(signed_id)
        self.assertEqual(user_id, self.author.id)

    #   The test sends a POST request to attempt logging in with incorrect credentials (correct email but wrong password).
	#   It verifies that the response returns an HTTP 200 OK status (indicating the page was rendered properly, but the login was not successful).
	#   It ensures that the login page template (login/login.html) is rendered again after the failed login attempt.
	#   It checks that the error message 'Invalid login credentials' is present in the context of the rendered login page, informing the user about the failed login attempt.
    #   Purpose: This test ensures that a login attempt with incorrect credentials (correct email but wrong password) fails as expected.
    def test_login_invalid_credentials(self):
        """Test that login fails with incorrect credentials."""
        response = self.client.post(self.login_url, {
            'email': self.author.email,
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/login.html')
        self.assertIn('Invalid login credentials', response.context['error'])


    #   The test sends a GET request to the login URL to load the login page.
    #   It verifies that the HTTP status code is 200 OK, indicating that the page was successfully rendered.
    #   It ensures that the login page template (login/login.html) is used to render the response.
    #   Purpose: This test verifies that a GET request to the login URL correctly renders the login page.
    def test_login_get_request(self):
        """Test that GET request renders the login page."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/login.html')


class SignupViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('signup')
        self.index_url = reverse('index')

    #   This test simulates a POST request to the signup URL with valid data for a new user.
    #   It asserts that the response is a redirect to the index page, and checks that the user is successfully created by querying the database to see if an entry exists for the new email.
    #   The test also verifies that a cookie is set with the signed user ID and that this ID matches the newly created user’s ID.
    #   Purpose: It ensures that a user can successfully sign up and is logged in with the correct user ID in the cookie
    def test_signup_success(self):
        """Test successful user signup."""
        response = self.client.post(self.signup_url, {
            'display_name': 'New User',
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123'
        })
        self.assertRedirects(response, self.index_url)
        self.assertTrue(Author.objects.filter(email='newuser@example.com').exists())
        signed_id = self.client.cookies.get('id').value
        user_id = signing.loads(signed_id)
        new_author = Author.objects.get(email='newuser@example.com')
        self.assertEqual(user_id, new_author.id)

    #   This test simulates a POST request with empty fields in the signup form.
    #   It asserts that the response returns a 200 OK status, meaning the form is re-rendered, and checks that the signup page template (signup.html) is used.
    #   The test also verifies that an appropriate error message ('All fields are required.') is displayed in the response context.
    #   Purpose: It ensures that missing required fields cause the signup process to fail and return an error.
    def test_signup_missing_fields(self):
        """Test signup failure when fields are missing."""
        response = self.client.post(self.signup_url, {
            'display_name': '',
            'email': '',
            'password': '',
            'confirm_password': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/signup.html')
        self.assertIn('All fields are required.', response.context['error'])


    #   This test simulates a POST request where the entered passwords do not match.
    #   It asserts that the response returns a 200 OK status and the signup page is rendered again.
    #   The test also checks that the error message ('Passwords do not match') is included in the response context, ensuring proper feedback to the user.
    #   Purpose: It ensures that mismatched passwords cause the signup process to fail with an appropriate error message.
    def test_signup_password_mismatch(self):
        """Test signup failure when passwords do not match."""
        response = self.client.post(self.signup_url, {
            'display_name': 'User',
            'email': 'user@example.com',
            'password': 'password1',
            'confirm_password': 'password2'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/signup.html')
        self.assertIn('Passwords do not match', response.context['error'])


    #   This test creates an existing user in the database and then simulates a POST request attempting to sign up with the same email.
    #   It asserts that the response status is 200 OK and the signup page is rendered, along with an error message ('Email is already registered') in the context.
    #   Purpose: It ensures that trying to sign up with an already registered email results in a failure and displays the correct error message.
    def test_signup_email_already_registered(self):
        """Test signup failure when email is already registered."""
        Author.objects.create(
            display_name='Existing User',
            email='existing@example.com',
            password='hashed_password'
        )
        response = self.client.post(self.signup_url, {
            'display_name': 'New User',
            'email': 'existing@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/signup.html')
        self.assertIn('Email is already registered', response.context['error'])


    #   This test simulates a GET request to the signup URL.
    #   It asserts that the response status is 200 OK and that the signup page template (signup.html) is rendered correctly.
    #   Purpose: It ensures that a GET request to the signup page correctly loads the signup form for the user.
    def test_signup_get_request(self):
        """Test that GET request renders the signup page."""
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/signup.html')


class AuthenticationMiddlewareTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.signup_url = reverse('signup')
        self.index_url = reverse('index')
        self.password = 'password123'
        self.hashed_password = hashlib.sha256(self.password.encode()).hexdigest()
        self.author = Author.objects.create(
            display_name='Test User',
            email='testuser@example.com',
            password=self.hashed_password
        )

    def test_middleware_allows_public_paths(self):
        """Test that middleware allows access to login and signup without authentication."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)

    def test_middleware_blocks_unauthenticated_access(self):
        """Test that middleware blocks access to protected pages when not authenticated."""
        response = self.client.get(self.index_url)
        self.assertRedirects(response, self.login_url)

    def test_middleware_allows_authenticated_access(self):
        """Test that middleware allows access when user is authenticated."""
        signed_id = signing.dumps(self.author.id)
        self.client.cookies['id'] = signed_id
        response = self.client.get(self.index_url)
        # Assuming 'index' view returns status code 200 for authenticated users
        self.assertEqual(response.status_code, 200)

    def test_middleware_handles_invalid_cookie(self):
        """Test that middleware handles invalid cookie gracefully."""
        # Set an invalid cookie
        self.client.cookies['id'] = 'invalid_signature'
        response = self.client.get(self.index_url)

        # Update the client's cookies to reflect the response
        self.client.cookies.update(response.cookies)

        # Check that the response marks the 'id' cookie for deletion (empty value and expired)
        self.assertEqual(response.cookies['id'].value, '')
        self.assertEqual(response.cookies['id']['max-age'], 0)

        # Manually clear the client's cookies to simulate the deletion
        self.client.cookies.clear()

        # Now check that the 'id' cookie is no longer present in the client's cookies
        self.assertNotIn('id', self.client.cookies)

    def test_middleware_handles_nonexistent_user(self):
        """Test that middleware handles non-existent user IDs."""
        # Set a signed user ID that doesn't exist in the database
        signed_id = signing.dumps(9999)  # Assuming this ID does not exist
        self.client.cookies['id'] = signed_id
        response = self.client.get(self.index_url)
        
        # Update the client's cookies with the response cookies to reflect deletion
        self.client.cookies.update(response.cookies)

        # Check that the response deletes the 'id' cookie by setting it to an empty string
        self.assertEqual(response.cookies['id'].value, '')
        self.assertEqual(response.cookies['id']['max-age'], 0)  # Ensure cookie is expired

        # Manually clear the client's cookies to simulate the deletion
        self.client.cookies.clear()

        # Check that the 'id' cookie is no longer present in the client's cookies
        self.assertNotIn('id', self.client.cookies)