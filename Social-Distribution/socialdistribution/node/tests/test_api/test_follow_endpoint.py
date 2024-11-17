from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from node.models import Author, Follow, AllowedNode
from base64 import b64encode
from urllib.parse import quote  # for URL encoding
import json

class FollowersApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

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

        # Set up Basic Auth headers
        valid_credentials = b64encode(b'nodeuser:nodepassword').decode('utf-8')
        self.auth_headers = {'HTTP_AUTHORIZATION': f'Basic {valid_credentials}'}

    def test_get_followers_list(self):
        """Test retrieving the list of followers for an author."""
        Follow.objects.create(follower="http://localhost:8000/api/authors/2", following="http://localhost:8000/api/authors/1", approved=True)
        Follow.objects.create(follower="http://localhost:8000/api/authors/3", following="http://localhost:8000/api/authors/1", approved=True)

        # Request followers list for author_1
        response = self.client.get(
            "http://localhost:8000/api/authors/1/followers", 
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
            self.assertTrue(followers[i]['id'].endswith(f"/api/authors/{i+2}"))
            self.assertEqual(followers[i]['host'], "http://localhost:8000/api/")
            self.assertEqual(followers[i]['displayName'], f"Test author {i+2}")
            self.assertEqual(followers[i]['github'], f"http://github.com/{i+2}")
            # self.assertEqual(followers[i]['profileImage'], f"http://imagehost.com/author{i+2}.png")
            self.assertEqual(followers[i]['page'], f"http://localhost:8000/authors/{i+2}")
        

    def test_add_follower(self):
        """Test adding a follower to an author."""
        url = f"http://localhost:8000/api/authors/{self.author_1.id}/followers/{quote('http://localhost:8000/api/authors/2', safe='')}"
        response = self.client.put(url, **self.auth_headers)

        # Check response
        self.assertIn(response.status_code, [200, 201])

        # Verify in database
        self.assertTrue(Follow.objects.filter(follower="http://localhost:8000/api/authors/2", following="http://localhost:8000/api/authors/1").exists())
        
    
    # def test_add_follower_without_authentication(self):
    #     """Test adding a follower to an author without valid authentication."""
    #     url = f"http://localhost:8000/api/authors/{self.author_1.id}/followers/{quote('http://localhost:8000/api/authors/2', safe='')}"
    #     invalid_credentials = b64encode(b'invalidnodeuser:nodepassword').decode('utf-8')

    #     response = self.client.put(url, {'HTTP_AUTHORIZATION': f'Basic {invalid_credentials}'})
        
    #     # Assert response
    #     self.assertIn(response.status_code, [401, 403])

    def test_remove_follower(self):
        """Test removing a follower from an author."""
        # Add author_2 as a follower of author_1
        Follow.objects.create(follower="http://localhost:8000/api/authors/2", following="http://localhost:8000/api/authors/1", approved=True)

        # Delete the follower relationship
        url = f"http://localhost:8000/api/authors/{self.author_1.id}/followers/{quote('http://localhost:8000/api/authors/2', safe='')}"
        response = self.client.delete(url, **self.auth_headers)

        # Assert response
        self.assertIn(response.status_code, [200, 204])

        # Verify removal in database
        self.assertFalse(Follow.objects.filter(follower="http://localhost:8000/api/authors/2", following="http://localhost:8000/api/authors/1").exists())


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
        Follow.objects.create(follower="http://localhost:8000/api/authors/2", following="http://localhost:8000/api/authors/1", approved=True)

        # Check if author_2 is a follower of author_1
        url = f"http://localhost:8000/api/authors/{self.author_1.id}/followers/{quote('http://localhost:8000/api/authors/2', safe='')}"
        print("test_check_if: ", url)
        response = self.client.get(url, **self.auth_headers)

        # Assert response
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(response_data['id'], f"http://localhost:8000/api/authors/{self.author_2.id}")


    def test_check_if_not_follower(self):
        """Test checking if a specific author is not a follower of another author."""
        # Check if author_2 is a follower of author_1 without any follow relationship
        url = f"http://localhost:8000/api/authors/{self.author_1.id}/followers/{quote('http://localhost:8000/api/authors/2', safe='')}"
        response = self.client.get(url, **self.auth_headers)

        # Assert response
        self.assertEqual(response.status_code, 404)


    def test_send_follow_request(self):
        """Test sending a follow request to an author's inbox."""
        follow_request_data = {
            "type": "follow",
            "summary": "Test author 2 wants to follow Test author 1",
            "actor": {
                "type": "author",
                "id": f"http://localhost:8000/api/authors/2",
                "host": "http://localhost:8000/api/",
                "displayName": "Test author 2",
                "github": "http://github.com/2",
                "profileImage": "http://imagehost.com/author2.png",
                "page": f"http://localhost:8000/authors/2"
            },
            "object": {
                "type": "author",
                "id": f"http://localhost:8000/api/authors/1",
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
        self.assertTrue(Follow.objects.filter(follower=f"http://localhost:8000/api/authors/2", following=f"http://localhost:8000/api/authors/1").exists())