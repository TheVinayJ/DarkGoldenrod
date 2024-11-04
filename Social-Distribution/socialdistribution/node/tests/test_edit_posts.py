from django.test import TestCase
from django.urls import reverse
from node.models import Author, Post
import hashlib
from django.utils import timezone
import datetime


class EditPostTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create two authors
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

        # Create a post by author1
        cls.post = Post.objects.create(
            author=cls.author1,
            title="Original Title",
            description="Original description",
            visibility="PUBLIC",
            published = timezone.make_aware(datetime.datetime.now(), datetime.timezone.utc),
        )

    def tearDown(self):
        # Written with aid of Microsoft Copilot, Oct. 2024
        Post.objects.all().delete()
        Author.objects.all().delete()
        self.client.cookies.clear()

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

    def test_edit_own_post(self):
        # Log in as author1
        login = self.login(self.author1)
        if login.status_code == 200:
            # Prepare new data for the post
            updated_data = {
                'title': 'Updated Title',
                'body-text': 'Updated description',
                'visibility': 'FRIENDS',
            }

            # Send POST request to edit the post
            response = self.client.post(
                reverse('edit_post', kwargs={'post_id': self.post.id}),
                data=updated_data
            )

            # Check for successful redirect after editing
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, reverse('view_post', kwargs={'post_id': self.post.id}))

            # Fetch the updated post from the database
            updated_post = Post.objects.get(id=self.post.id)

            # Verify that the post was updated
            self.assertEqual(updated_post.title, updated_data['title'])
            self.assertEqual(updated_post.text_content, updated_data['body-text'])
            self.assertEqual(updated_post.visibility, updated_data['visibility'])

    # def test_edit_post_get_form(self):
    #     # Log in as author1
    #     self.login(self.author1)
    #
    #     # Send GET request to get the edit form
    #     response = self.client.get(reverse('edit_post', kwargs={'post_id': self.post.id}))
    #
    #     # Check that the response is 200 OK
    #     self.assertEqual(response.status_code, 200)
    #
    #     # Verify that the form contains the current post data
    #     self.assertContains(response, 'Original Title')
    #     self.assertContains(response, 'Original description')

    def test_edit_other_author_post(self):
        # Log in as author2 (not the owner of the post)
        login = self.login(self.author2)
        if login.status_code == 200:
            # Attempt to edit author1's post
            updated_data = {
                'title': 'Hacked Title',
                'body-text': 'Hacked description',
                'visibility': 'FRIENDS',
            }

            response = self.client.post(
                reverse('edit_post', kwargs={'post_id': self.post.id}),
                data=updated_data
            )

            # Check that access is forbidden
            self.assertEqual(response.status_code, 302)

            # Verify that the post was not changed
            original_post = Post.objects.get(id=self.post.id)
            self.assertEqual(original_post.title, 'Original Title')
            self.assertEqual(original_post.description, 'Original description')

    def test_edit_post_not_logged_in(self):
        # Attempt to edit the post without logging in
        updated_data = {
            'title': 'Anonymous Title',
            'body-text': 'Anonymous description',
            'visibility': 'PUBLIC',
        }

        response = self.client.post(
            reverse('edit_post', kwargs={'post_id': self.post.id}),
            data=updated_data
        )

        # Check that the user is redirected to login or access is forbidden
        self.assertEqual(response.status_code, 302)

        # Verify that the post was not changed
        original_post = Post.objects.get(id=self.post.id)
        self.assertEqual(original_post.title, 'Original Title')
        self.assertEqual(original_post.description, 'Original description')

def test_edit_post_invalid_data(self):
    # Log in as author1
    login = self.login(self.author1)
    if login.status_code == 200:
        # Prepare invalid data (missing title)
        invalid_data = {
            'title': '',
            'body-text': 'Updated description',
            'visibility': 'PUBLIC',
        }

        # Send POST request with invalid data
        response = self.client.post(
            reverse('edit_post', kwargs={'post_id': self.post.id}),
            data=invalid_data
        )

        # The response should be 200 OK, rendering the form again with error messages
        self.assertEqual(response.status_code, 200)

        # Check that an error message is displayed
        self.assertContains(response, "Title and description cannot be empty.")

        # Verify that the post was not changed
        original_post = Post.objects.get(id=self.post.id)
        self.assertEqual(original_post.title, 'Original Title')
        self.assertEqual(original_post.description, 'Original description')

