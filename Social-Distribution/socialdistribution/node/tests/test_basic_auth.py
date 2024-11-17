# node/tests/test_basic_auth.py

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from node.models import AllowedNode, Author  # Adjust the import paths as needed
from django.contrib.auth.hashers import make_password, check_password
from base64 import b64encode
       
class NodeAuthenticationTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create an Author instance as the user for 'added_by' in AllowedNode
        self.admin_user = Author.objects.create_user(
            email="admin@example.com",
            display_name="Admin User",
            password="adminpass"
        )

        # Create an AllowedNode instance associated with this Author
        # Use raw password here, let the model's save method handle hashing
        self.node = AllowedNode.objects.create(
            url="http://remote-node.com",
            username="nodeuser",
            password="nodepassword",
            is_active=True
        )

    def test_node_basic_auth_success(self):
        # Encode the username and password for Basic Auth
        auth_credentials = b64encode(b'nodeuser:nodepassword').decode('utf-8')
        
        response = self.client.get(
            reverse('index'),
            HTTP_AUTHORIZATION=f'Basic {auth_credentials}'
        )
        self.assertEqual(response.status_code, 200)

    def test_node_basic_auth_failure(self):
        # Encode invalid credentials for Basic Auth
        invalid_credentials = b64encode(b'nodeuser:wrongpassword').decode('utf-8')
        
        response = self.client.get(
            reverse('index'),
            HTTP_AUTHORIZATION=f'Basic {invalid_credentials}'
        )
        self.assertEqual(response.status_code, 401)