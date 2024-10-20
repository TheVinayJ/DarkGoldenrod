from django.test import TestCase
from node.models import Post, Repost, Author, Follow
from django.urls import reverse
import hashlib

class RepostTests(TestCase):
    def setUp(cls):
        # Create two authors
        cls.author1 = Author.objects.create(display_name='Author 1', email="author1@example.com", password=hashlib.sha256("password123".encode()).hexdigest())
        cls.author2 = Author.objects.create(display_name='Author 2', email="author2@example.com", password=hashlib.sha256("password123".encode()).hexdigest())

        # Create a post by Author 1
        cls.post = Post.objects.create(
            author=cls.author1,
            title="Original Post",
            description="Original post description",
            text_content="This is the content of the original post",
            visibility="PUBLIC"
        )

        # Create a follow relationship (Author 2 follows Author 1)
        Follow.objects.create(follower="http://darkgoldenrod/api/authors/" + str(cls.author1.id), following="http://darkgoldenrod/api/authors/" + str(cls.author2.id))

    def login(self, author):
        # Helper method to log in an author
        login_data = {
            'email': author.email,
            'password': 'password123',
        }
        response = self.client.post(reverse('login'), login_data)
        self.assertEqual(response.status_code, 302)

    def test_create_repost(self):
        self.login(self.author1)
        # Create a repost of the original post by Author 2
        repost = Repost.objects.create(
            original_post=self.post,
            shared_by=self.author2
        )

        # Verify the repost exists in the database
        self.assertEqual(Repost.objects.count(), 1)

    def test_repost_appears_in_feed(self):
        self.login(self.author1)
        repost = Repost.objects.create(
            original_post=self.post,
            shared_by=self.author2
        )

        # Fetch the feed of Author 1
        response = self.client.get(reverse('following_feed'))

        # Check that the repost appears in the feed
        self.assertContains(response, repost.shared_by)

    def test_repost_private_post_forbidden(self):
        self.login(self.author1)
        # Make the post for FRIENDS (not PUBLIC)
        self.post.visibility = "FRIENDS"
        self.post.save()

        # Attempt to repost and expect a forbidden response
        response = self.client.post(reverse('repost', kwargs={'id': self.post.id}))
        self.assertEqual(response.status_code, 403)  

        # Make post UNLISTED
        self.post.visibility = "UNLISTED"
        self.post.save()

        # Attempt to repost and expect a forbidden response
        response = self.client.post(reverse('repost', kwargs={'id': self.post.id}))
        self.assertEqual(response.status_code, 403)  
