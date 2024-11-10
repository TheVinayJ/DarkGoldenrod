from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from node.models import Author, AllowedNode
from django.contrib.auth.hashers import make_password
from base64 import b64encode

class AuthorsApiTest(TestCase):
    def setUp(self):
        # Initialize test client
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
            url="http://localhost:8000/",
            username="nodeuser",
            password="nodepassword",
            is_active=True
        )
        
        # Create several authors for pagination tests
        self.authors = [
            Author.objects.create(
                email=f"user{i}@example.com",
                password=f"strongpassword@{i}",
                display_name=f"Test author {i}",
                github=f"http://github.com/{i}",
                profile_image=f"http://imagehost.com/author{i}.png",
                page=f"http://localhost:8000/authors/{i}",
                host="http://localhost:8000/api/"
            ) for i in range(1,51,1)  # Creating 50 authors
        ]

        # Set up authentication credentials
        auth_credentials = b64encode(b'nodeuser:nodepassword').decode('utf-8')
        self.auth_headers = {'HTTP_AUTHORIZATION': f'Basic {auth_credentials}'}
        
        
    def print_all_authors_from_response(self, response_data, test_case):
        print(f"\n\n{test_case}")
        authors = response_data['authors']
        for i in range(len(authors)):
            print("{")
            for key, value in authors[i].items():
                print(f"\t{key}: {value}")
            print("}\n")
            
            
    def print_single_author_from_response(self, author, test_case):
        print(f"\n\n{test_case}")
        print("{")
        for key, value in author.items():
            print(f"\t{key}: {value}")
        print("}\n")
        
        
    def test_get_author_with_invalid_remote_node(self):
        """Test retrieving authors with the node that is not in allowed node."""
            
        invalid_auth_credentials = b64encode(b'invalidnodeuser:nodepassword').decode('utf-8')
            
        response = self.client.get(
            "http://localhost:8000/api/authors/",
            HTTP_AUTHORIZATION=f'Basic {invalid_auth_credentials}'
        )
    
        # Check the response status code
        self.assertEqual(response.status_code, 401)
        
        
    def test_get_author_with_wrong_authentication(self):
        """Test retrieving authors with wrong authentication."""
        
        invalid_auth_credentials = b64encode(b'nodeuser:wrongnodepassword').decode('utf-8')
        
        response = self.client.get(
            "http://localhost:8000/api/authors/",
            HTTP_AUTHORIZATION=f'Basic {invalid_auth_credentials}'
        )

        # Check the response status code
        self.assertEqual(response.status_code, 401)
        
        
    def test_get_authors(self):
        """Test retrieving all authors from the database."""
        
        DEBUG = False
        
        # Send request with pagination parameters
        response = self.client.get(
            "http://localhost:8000/api/authors/",
            **self.auth_headers
        )
        
        # Parse JSON response
        response_data = response.json()

        # Check the response status code
        self.assertEqual(response.status_code, 200)
        
        try:
            # Check the structure of the response data
            self.assertEqual(len(response_data['authors']), 50, f"Expected 50 authors in the response, but got {len(response_data['authors'])} authors from the response")
            self.assertEqual(response_data['type'], "authors")
        except AssertionError as e:
            if DEBUG:
                self.print_all_authors_from_response(response_data, "test_get_authors")
            self.fail()
        
        
    def test_get_authors_paginated(self):
        """Test retrieving authors with pagination parameters (first page with 5 authors)."""

        DEBUG = False
        
        # Send request with pagination parameters
        response = self.client.get(
            "http://localhost:8000/api/authors/?page=1&size=5",
            **self.auth_headers
        )

        # Parse JSON response
        response_data = response.json()

        # Check the response status code
        self.assertEqual(response.status_code, 200)

        # Check the structure of the response data
        try:
            self.assertEqual(
                len(response_data['authors']), 5,
                f"Expected 5 authors in the response, but got {len(response_data['authors'])} authors from the response"
            )
        except AssertionError as e:
            if DEBUG:
                self.print_all_authors_from_response(response_data, "test_get_authors_paginated")
            self.fail()

        self.assertEqual(response_data['type'], "authors")
        
        authors = response_data['authors']
        
        # Check the first author in the response
        
        for i in range(5):
            try:
                # Test type in response
                self.assertIn(
                    'type',
                    authors[i],
                    f"\nAuthor {i + 1} is missing 'type' key"
                )
                self.assertEqual(
                    authors[i]['type'], 
                    'author', 
                    f"\nAuthor {i + 1} type should be 'author'"
                )
                
                # Test id in response
                self.assertIn(
                    'id',
                    authors[i],
                    f"\nAuthor {i + 1} is missing 'id' key"
                )
                self.assertTrue(
                    authors[i]['id'].endswith(f"/api/authors/{i + 1}"),
                    f"\nAuthor {i + 1} id should end with '/api/authors/{i + 1}', but response return '{authors[i]['id']}'"
                )
                
                # Test host in response
                self.assertIn(
                    'host',
                    authors[i],
                    f"\nAuthor {i + 1} is missing 'host' key"
                )
                self.assertEqual(
                    authors[i]['host'],
                    'http://localhost:8000/api/',
                    f"\nAuthor {i + 1} host should be 'http://localhost:8000/api/', but response return '{authors[i]['host']}'"
                )
                
                # Test displayName in response
                self.assertIn(
                    'displayName',
                    authors[i],
                    f"\n\nAuthor {i + 1} is missing 'displayName' key"
                )
                self.assertEqual(
                    authors[i]['displayName'],
                    f"Test author {i + 1}",
                    f"\nAuthor {i + 1} display name should be 'Test author{i + 1}', but response return '{authors[i]['displayName']}'"
                )
                
                # Test github in response
                self.assertIn(
                    'github',
                    authors[i],
                    f"\nAuthor {i + 1} is missing 'github' key"
                )
                self.assertEqual(
                    authors[i]['github'],
                    f"http://github.com/{i + 1}",
                    f"\nAuthor {i + 1} url should be 'http://github.com/{i + 1}', but response return '{authors[i]['github']}'"
                )
                
                # Test profileImage in response
                self.assertIn( 
                    'profileImage', 
                    authors[i],
                    f"\nAuthor {i + 1} is missing 'profileImage' key"
                )
                
                # Test page in response
                self.assertIn(
                    'page', 
                    authors[i],
                    f"\nAuthor {i + 1} is missing 'page' key"
                )
                self.assertTrue(
                    str(authors[i]['page']).endswith(f"/authors/{i + 1}"),
                    f"\nAuthor {i + 1} page should end with '/authors/{i + 1}', but response return '{authors[i]['page']}'"
                )
            except AssertionError as e:
                if DEBUG:
                    self.print_single_author_from_response(authors[i], "test_get_authors_paginated")
                self.fail()
    
    
    def test_get_authors_with_different_page(self):
        """Test retrieving 5 authors, authors 45 to 49 from the database."""
        
        DEBUG = False

        # Send request with pagination parameters
        response = self.client.get(
            "http://localhost:8000/api/authors/?page=10&size=5",
            **self.auth_headers
        )

        # Parse JSON response
        response_data = response.json()

        # Check the response status code
        self.assertEqual(response.status_code, 200)

        # Check the structure of the response data
        try:
            self.assertEqual(len(response_data['authors']), 5, f"Expected 5 authors in the response (Test author 46-50 or index 45-49 in the database), but got {len(response_data['authors'])} authors from the response")
        except AssertionError as e:
            if DEBUG:
                self.print_all_authors_from_response(response_data, "test_get_authors_with_different_page")
            self.fail()
        
        self.assertEqual(response_data['type'], "authors")
        
        authors = response_data['authors']
        
        # Check the first author in the response
        
        for i in range(45, 50, 1):
            try:
                # Test type in response
                self.assertIn(
                    'type',
                    authors[i - 45],
                    f"\nAuthor {i + 1} is missing 'type' key"
                )
                self.assertEqual(
                    authors[i - 45]['type'], 
                    'author', 
                    f"\nAuthor {i + 1} type should be 'author'"
                )
                
                # Test id in response
                self.assertIn(
                    'id',
                    authors[i - 45],
                    f"\nAuthor {i + 1} is missing 'id' key"
                )
                self.assertTrue(
                    authors[i - 45]['id'].endswith(f"/api/authors/{i + 1}"),
                    f"\nAuthor {i + 1} id should end with '/api/authors/{i + 1}', but response return '{authors[i - 45]['id']}'"
                )
                
                # Test host in response
                self.assertIn(
                    'host',
                    authors[i - 45],
                    f"\nAuthor {i + 1} is missing 'host' key"
                )
                self.assertEqual(
                    authors[i - 45]['host'],
                    'http://localhost:8000/api/',
                    f"\nAuthor {i + 1} host should be 'http://localhost:8000/api/', but response return '{authors[i - 45]['host']}'"
                )
                
                # Test displayName in response
                self.assertIn(
                    'displayName',
                    authors[i - 45],
                    f"\n\nAuthor {i + 1} is missing 'displayName' key"
                )
                self.assertEqual(
                    authors[i - 45]['displayName'],
                    f"Test author {i + 1}",
                    f"\nAuthor {i + 1} display name should be 'Test author{i + 1}', but response return '{authors[i - 45]['displayName']}'"
                )
                
                # Test github in response
                self.assertIn(
                    'github',
                    authors[i - 45],
                    f"\nAuthor {i + 1} is missing 'github' key"
                )
                self.assertEqual(
                    authors[i - 45]['github'],
                    f"http://github.com/{i + 1}",
                    f"\nAuthor {i + 1} url should be 'http://github.com/{i + 1}', but response return '{authors[i - 45]['github']}'"
                )
                
                # Test profileImage in response
                self.assertIn( 
                    'profileImage', 
                    authors[i - 45],
                    f"\nAuthor {i + 1} is missing 'profileImage' key"
                )
                
                # Test page in response
                self.assertIn(
                    'page', 
                    authors[i - 45],
                    f"\nAuthor {i + 1} is missing 'page' key"
                )
                self.assertTrue(
                    str(authors[i - 45]['page']).endswith(f"/authors/{i + 1}"),
                    f"\nAuthor {i + 1} page should end with '/authors/{i + 1}', but response return '{authors[i - 45]['page']}'"
                )
            except AssertionError as e:
                if DEBUG:
                    self.print_single_author_from_response(authors[i - 45], "test_get_authors_with_different_page")
                self.fail()
            
            
    def test_get_single_author(self):
        """Test get a single author from the database."""
        DEBUG = False

        # Send request with pagination parameters
        response = self.client.get(
            "http://localhost:8000/api/authors/1",
            **self.auth_headers
        )

        print(response)
        # Parse JSON response
        response_data = response.json()
        
        # Check the response status code
        self.assertEqual(response.status_code, 200, f"Expected status code 200, but got {response.status_code}")
        
        # Test type in response
        self.assertIn(
            'type',
            response_data,
            f"\nAuthor 1 is missing 'type' key"
        )
        self.assertEqual(
        response_data['type'], 
            'author', 
            f"\nAuthor 1 type should be 'author'"
        )
                
        # Test id in response
        self.assertIn(
            'id',
            response_data,
            f"\nAuthor 1 is missing 'id' key"
        )
        self.assertTrue(
            str(response_data['id']).endswith(f"/api/authors/1"),
            f"\nAuthor 1 id should end with '/api/authors/1', but response return '{response_data['id']}'"
        )
                
        # Test host in response
        self.assertIn(
            'host',
            response_data,
            f"\nAuthor 1 is missing 'host' key"
        )
        self.assertEqual(
            response_data['host'],
            'http://localhost:8000/api/',
            f"\nAuthor 1 host should be 'http://localhost:8000/api/', but response return '{response_data['host']}'"
        )
                
        # Test displayName in response
        self.assertIn('displayName', response_data, f"\n\nAuthor 1 is missing 'displayName' key")
        self.assertEqual(response_data['displayName'], f"Test author 1", f"\nAuthor 1 display name should be 'Test author 1', but response return '{response_data['displayName']}'")
                
        # Test github in response
        self.assertIn('github', response_data, f"\nAuthor 1 is missing 'github' key")
        self.assertEqual(response_data['github'], f"http://github.com/1", f"\nAuthor 1 url should be 'http://github.com/1', but response return '{response_data['github']}'")

        # Test profileImage in response
        self.assertIn('profileImage', response_data, f"\nAuthor 1 is missing 'profileImage' key")
                
        # Test page in response
        self.assertIn('page', response_data, f"\nAuthor 1 is missing 'page' key")
        self.assertTrue(str(response_data['page']).endswith(f"/authors/1"), f"\nAuthor 1 page should end with '/authors/1', but response return '{response_data['page']}'")
        
    
    def test_put_author(self):
        """Test updating an author's information."""
        
        DEBUG = False
        
        updated_data = {
            "display_name": "Test author 1 - Updated",
        }
        
        response = self.client.get(
            "http://localhost:8000/api/authors/1",
            data=updated_data,
            content_type='application/json',
            **self.auth_headers
        )
        
        response_data = response.json()
        
        # Check the response status code
        self.assertEqual(response.status_code, 200, f"Expected status code 200, but got {response.status_code}")
        
        response = self.client.get(
            "http://localhost:8000/api/authors/1",
            **self.auth_headers
        )
        
        response_data = response.json()
        
        # Check the response status code
        self.assertEqual(response.status_code, 200, f"Expected status code 200, but got {response.status_code}")
        
        # Test type in response
        self.assertIn('type', response_data, f"\nAuthor 1 is missing 'type' key")
        self.assertEqual(response_data['type'], 'author', f"\nAuthor 1 type should be 'author'")
        
        # Test id in response
        self.assertIn('id', response_data, f"\nAuthor 1 is missing 'id' key")
        self.assertTrue(str(response_data['id']).endswith(f"/api/authors/1"), f"\nAuthor 1 id should end with '/api/authors/1', but response return '{response_data['id']}'")
                
        # Test host in response
        self.assertIn('host', response_data, f"\nAuthor 1 is missing 'host' key")
        self.assertEqual(response_data['host'], 'http://localhost:8000/api/', f"\nAuthor 1 host should be 'http://localhost:8000/api/', but response return '{response_data['host']}'")
                
        # Test displayName in response
        self.assertIn('displayName', response_data, f"\n\nAuthor 1 is missing 'displayName' key")
        self.assertEqual(response_data['displayName'], f"Test author 1 - Updated", f"\nAuthor 1 display name should be 'Test author 1', but response return '{response_data['displayName']}'")
                
        # Test github in response
        self.assertIn('github', response_data, f"\nAuthor 1 is missing 'github' key")
        self.assertEqual(response_data['github'], f"http://github.com/1", f"\nAuthor 1 url should be 'http://github.com/1', but response return '{response_data['github']}'")

        # Test profileImage in response
        self.assertIn('profileImage', response_data, f"\nAuthor 1 is missing 'profileImage' key")
                
        # Test page in response
        self.assertIn('page', response_data, f"\nAuthor 1 is missing 'page' key")
        self.assertTrue(str(response_data['page']).endswith(f"/authors/1"),f"\nAuthor 1 page should end with '/authors/1', but response return '{response_data['page']}'")
