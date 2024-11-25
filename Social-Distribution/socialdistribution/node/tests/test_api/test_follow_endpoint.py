from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from node.models import Author, Follow, AllowedNode
from base64 import b64encode
from urllib.parse import quote  # for URL encoding
import json
from django.contrib.auth import get_user_model

User = get_user_model()

class FollowersApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('api_login') 
        self.logout_url = reverse('api_logout')
        # Create an AllowedNode instance associated with this Author
        # Use raw password here, let the model's save method handle hashing
        self.node = AllowedNode.objects.create(
            url="http://localhost:8000/",
            username="nodeuser",
            password="nodepassword",
            is_active=True
        )

        # Create two authors for testing
        self.author_1 = Author.objects.create(
            email=f"user1@example.com",
            password=f"strongpassword@1",
            display_name=f"Test author 1",
            github=f"http://github.com/1",
            profile_image=f"http://imagehost.com/author1.png",
            page=f"http://localhost:8000/authors/1",
            host="http://localhost:8000/api/"
        )
        
        self.author_2 = Author.objects.create(
            email=f"user2@example.com",
            password=f"strongpassword@2",
            display_name=f"Test author 2",
            github=f"http://github.com/2",
            profile_image=f"http://imagehost.com/author2.png",
            page=f"http://localhost:8000/authors/2",
            host="http://localhost:8000/api/"
        )
        
        self.author_3 = Author.objects.create(
            email=f"user3@example.com",
            password=f"strongpassword@3",
            display_name=f"Test author 3",
            github=f"http://github.com/3",
            profile_image=f"http://imagehost.com/author3.png",
            page=f"http://localhost:8000/authors/3",
            host="http://localhost:8000/api/"
        )

        # Create a user for testing login and logout
        self.test_user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword123',
            display_name='Test User'
        )

        # Set up Basic Auth headers
        valid_credentials = b64encode(b'nodeuser:nodepassword').decode('utf-8')
        self.auth_headers = {'HTTP_AUTHORIZATION': f'Basic {valid_credentials}'}

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
            format='json',
        )
        return response

    def test_get_followers_list(self):
        """Test retrieving the list of followers for an author."""
        Follow.objects.create(follower=self.author_2.url, following=self.author_1.url, approved=True)
        Follow.objects.create(follower=self.author_3.url, following=self.author_1.url, approved=True)

        login_response = self.login_user()
        self.assertIn(login_response.status_code, [200, 201, 204])

        # Request followers list for author_1
        response = self.client.get(
            f"{self.author_1.url}/followers", 
            **self.auth_headers
        )

        # Assert response
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        print("response_data: ", response_data)
        
        self.assertIn('type', response_data)
        self.assertEqual(response_data['type'], 'followers')
        
        followers = response_data['followers']
        print(followers)
        
        self.assertTrue(len(followers) == 2)
        
        for i in range(len(followers)):
            self.assertIn('type', followers[i])
            self.assertIn('id', followers[i])
            self.assertIn('host', followers[i])
            self.assertIn('displayName', followers[i])
            self.assertIn('page', followers[i])
            self.assertIn('github', followers[i])
            self.assertIn('profileImage', followers[i])
            
            self.assertEqual(followers[i]['type'], 'author')
            self.assertEqual(followers[i]['host'], "http://localhost:8000/api/")
            self.assertEqual(followers[i]['displayName'], f"Test author {i+2}")
            self.assertEqual(followers[i]['github'], f"http://github.com/{i+2}")
            # self.assertEqual(followers[i]['profileImage'], f"http://imagehost.com/author{i+2}.png")
            self.assertEqual(followers[i]['page'], f"http://localhost:8000/authors/{i+2}")
        

    def test_add_follower(self):
        """Test adding a follower to an author."""
        login_response = self.login_user()
        self.assertIn(login_response.status_code, [200, 201, 204])
        Follow.objects.create(follower=self.author_2.url, following=self.test_user.url, approved=False)
        url = f"{self.test_user.url}/followers/{quote(self.author_2.url, safe='')}"
        print("add follower url: ", url)
        response = self.client.put(url, **self.auth_headers)

        # Check response
        self.assertIn(response.status_code, [200, 201])

        # Verify in database
        self.assertTrue(Follow.objects.filter(follower=self.author_2.url, following=self.test_user.url).exists())
        
    
    # def test_add_follower_without_authentication(self):
    #     """Test adding a follower to an author without valid authentication."""
    #     url = f"http://localhost:8000/api/authors/{self.author_1.id}/followers/{quote(self.author_2.url, safe='')}"
    #     invalid_credentials = b64encode(b'invalidnodeuser:nodepassword').decode('utf-8')

    #     response = self.client.put(url, {'HTTP_AUTHORIZATION': f'Basic {invalid_credentials}'})
        
    #     # Assert response
    #     self.assertIn(response.status_code, [401, 403])

    def test_remove_follower(self):
        """Test removing a follower from an author."""
        # Add author_2 as a follower of author_1
        login_response = self.login_user()
        self.assertIn(login_response.status_code, [200, 201, 204])
        Follow.objects.create(follower=self.author_1.url, following=self.test_user.url, approved=True)

        # Delete the follower relationship
        url = f"{self.test_user.url}/followers/{quote(self.author_1.url, safe='')}"
        print("test_user url: ", self.test_user.url)
        response = self.client.delete(url, **self.auth_headers)

        # Assert response
        self.assertIn(response.status_code, [200, 204])

        # Verify removal in database
        self.assertFalse(Follow.objects.filter(follower=self.author_1.url, following=self.test_user.url).exists())


    # def test_remove_follower_without_authentication(self):
    #     """Test removing a follower from an author without valid authentication."""
    #     # Add author_2 as a follower of author_1
    #     Follow.objects.create(follower=self.author_2, following=self.author_1)
        
    #     invalid_credentials = b64encode(b'invalidnodeuser:nodepassword').decode('utf-8')

    #     # Delete the follower relationship
    #     url = f"http://localhost:8000/api/authors/{self.author_1.id}/followers/{quote(self.author_2.id)}"
    #     response = self.client.delete(url, {'HTTP_AUTHORIZATION': f'Basic {invalid_credentials}'})

    #     # Assert response
    #     self.assertIn(response.status_code, [401, 403])
        

    def test_check_if_follower(self):
        """Test checking if a specific author is a follower of another author."""
        # Add author_2 as a follower of author_1
        DEBUG = True
        login_response = self.login_user()
        self.assertIn(login_response.status_code, [200, 201, 204])
        Follow.objects.create(follower=self.author_2.url, following=self.author_1.url, approved=True)

        # Check if author_2 is a follower of author_1
        url = f"http://localhost:8000/api/authors/{self.author_1.id}/followers/{quote(self.author_2.url, safe='')}"
        if DEBUG:
            print("test_check_if: ", url)
        response = self.client.get(url, **self.auth_headers)

        # Assert response
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        if DEBUG:
            print("response line 203: ", response_data)
        self.assertEqual(response_data['id'], self.author_2.url)


    def test_check_if_not_follower(self):
        """Test checking if a specific author is not a follower of another author."""
        login_response = self.login_user()
        self.assertIn(login_response.status_code, [200, 201, 204])
        # Check if author_2 is a follower of author_1 without any follow relationship
        url = f"http://localhost:8000/api/authors/{self.author_1.id}/followers/{quote(self.author_2.url, safe='')}"
        response = self.client.get(url, **self.auth_headers)

        # Assert response
        self.assertEqual(response.status_code, 404)


    def test_send_follow_request(self):
        """Test sending a follow request to an author's inbox."""
        login_response = self.login_user()
        self.assertIn(login_response.status_code, [200, 201, 204])
        follow_request_data = {
            "type": "follow",
            "summary": "Test author 2 wants to follow Test author 1",
            "actor": {
                "type": "author",
                "id": self.author_2.url,
                "host": "http://localhost:8000/api/",
                "displayName": "Test author 2",
                "github": "http://github.com/2",
                "profileImage": "http://imagehost.com/author2.png",
                "page": f"http://localhost:8000/authors/2"
            },
            "object": {
                "type": "author",
                "id": self.author_1.url,
                "host": "http://localhost:8000/api/",
                "displayName": "Test author 1",
                "github": "http://github.com/1",
                "profileImage": "http://imagehost.com/author1.png",
                "page": f"http://localhost:8000/authors/1"
            }
        }

        # Send follow request
        url = f"http://localhost:8000/api/authors/{self.author_1.id}/inbox/"
        response = self.client.post(url, data=json.dumps(follow_request_data), content_type="application/json", **self.auth_headers)

        print(response.content)
        # Assert response
        self.assertIn(response.status_code, [200, 201])
        self.assertTrue(Follow.objects.filter(follower=self.author_2.url, following=self.author_1.url).exists())