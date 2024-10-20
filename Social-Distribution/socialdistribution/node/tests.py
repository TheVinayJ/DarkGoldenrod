from django.test import TestCase, Client
from .models import *
from django.urls import reverse
from django.core import signing
from http.client import responses

from django.core import signing
from django.urls import reverse

from .models import *
from django.test import TestCase, Client
from . import views

# Create your tests here.
class ProfileTests(TestCase):
    def setUp(self):
        self.author1 = Author.objects.create(id=1, display_name="Test Author1", description="Test Description", github="torvalds")
        self.author2 = Author.objects.create(id=2, display_name="Test Author2")
        # author 2 is following author 1 (but is not followed back)
        self.follow1 = Follow.objects.create(follower="http://darkgoldenrod/api/authors/"+ str(self.author2.id),
                                             following="http://darkgoldenrod/api/authors/"+ str(self.author1.id))

        # cannot customize published date due to auto_now_add=True
        self.post1 = Post.objects.create(
            id = 1,
            title="Post 1",
            description="Description 1",
            text_content="Content 1",
            author=self.author1,
            # published='2023-10-18T10:00:00Z',
            visibility="PUBLIC"
        )
        self.post2 = Post.objects.create(
            title="Post 2",
            description="Description 2",
            text_content="Content 2",
            author=self.author1,
            # published='2024-10-19T10:00:00Z',
            visibility="PUBLIC"
        )

        self.post3 = Post.objects.create(
            title="Post 3",
            description="Happy New Millennium",
            text_content="Content 3",
            author=self.author1,
            # published='2000-01-01T10:00:00Z',
            visibility="FRIENDS" # friends only post
        )

        self.client = Client()

    def set_signed_id(self, author):
        signed_id = signing.dumps(author.id)
        self.client.cookies['id'] = signed_id

    def testAuthorContent(self):
        self.set_signed_id(self.author1)
        response = self.client.get(reverse('profile', args=[self.author1.id]))
        # make sure author's info displayed correct
        self.assertContains(response, "Test Author1")  # Check display name
        self.assertContains(response, "Test Description")  # Check description
        self.assertEqual(response.status_code, 200)

    def testGithubActivity(self):
        self.set_signed_id(self.author1)
        response = self.client.get(reverse('profile', args=[self.author1.id]))
        self.assertTrue(response.context['activity']) # make sure GitHub section not empty

    def testEditProfile(self):
        self.set_signed_id(self.author1)

        new_data = {
            'display_name': 'Updated Author',
            'description': 'Updated Description',
        }
        response = self.client.post(reverse('profile_edit', args=[self.author1.id]), new_data)
        self.author1.refresh_from_db()
        self.assertEqual(self.author1.display_name, 'Updated Author')
        self.assertEqual(self.author1.description, 'Updated Description')
        self.assertRedirects(response, reverse('profile', args=[self.author1.id])) # check if redirect properly
        self.assertEqual(response.status_code, 302) # new edited data successfully moved

    def testPostOrder(self):
        self.set_signed_id(self.author1)

        response = self.client.get(reverse('profile', args=[self.author1.id]))
        posts = response.context['posts']
        # make sure most recent posts first
        self.assertEqual(posts[0], self.post3)  # recent post, last created in setUp
        self.assertEqual(posts[1], self.post2)  # older post

    def testFriendPostVisibility(self):
        self.set_signed_id(self.author2)

        response = self.client.get(
            reverse('profile', args=[self.author1.id]))  # viewing their author1(who does not follow back) profile
        posts = response.context['posts']
        self.assertNotIn(self.post3, posts)

class EditPostTests(TestCase):
    def setUp(self):
        self.author1 = Author.objects.create(id=1, display_name="Test Author1", description="Test Description", github="torvalds")
        self.author2 = Author.objects.create(id=2, display_name="Test Author2")

        # cannot customize published date due to auto_now_add=True
        self.post1 = Post.objects.create(
            id = 1,
            title="Post 1",
            description="Description 1",
            text_content="Content 1",
            author=self.author1,
            # published='2023-10-18T10:00:00Z',
            visibility="PUBLIC"
          
    def testOtherAuthorsCannotModify(self):
        signed_id = signing.dumps(self.author2.id)
        self.client.cookies['id'] = signed_id

        response = self.client.get(reverse('view_post', args=[self.post1.id]))
        self.assertNotContains(response, 'Edit Post')

    def testEditPost(self):
        signed_id = signing.dumps(self.author1.id)
        self.client.cookies['id'] = signed_id

        new_data = {
            'title': 'Updated Title',
            'description': 'Updated Description',
        }

        response = self.client.post(reverse('edit_post', args=[self.post1.id]), new_data)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.title, 'Updated Title')
        self.assertEqual(self.post1.description, 'Updated Description')
        self.assertRedirects(response, reverse('view_post', args=[self.post1.id]))  # check if redirect properly
        self.assertEqual(response.status_code, 302)  # new edited data successfully moved


class PostTests(TestCase):
    def setUp(self):

        self.author = Author.objects.create(display_name="Test Author")
        self.post = Post.objects.create(
            title="Test Title",
            description="Test Description",
            text_content="Test Content",
            author=self.author,
            visibility="PUBLIC"
        )

        self.private_post = Post.objects.create(
            title="Private Title",
            description="Test Description",
            text_content="Test Content",
            author=None,
            visibility="PRIVATE"
        )

        self.comment = Comment.objects.create(
            author=self.author,
            post=self.post,
            text="Test Comment text"
        )

        self.friend_author = Author.objects.create(display_name="Test Friend")

        self.friends_post = Post.objects.create(
            title="Private Title",
            description="Test Description",
            text_content="Test Content",
            author=self.friend_author,
            visibility="FRIENDS"
        )

        self.client = Client()

    def test_post_creation(self):
            self.assertEqual(self.post.title, "Test Title")
            self.assertEqual(self.post.author.display_name, "Test Author")

    def test_add_post(self):
            response = self.client.get(reverse('add'), follow=True)
            self.assertEqual(response.status_code, 200)
            response = self.client.post(reverse(views.save), {'title': 'New Post',
                                                          'body-text': 'Test Description',
                                                          'visibility': 'PUBLIC'})
            self.assertEqual(response.status_code, 302)
            self.assertTrue(Post.objects.filter(title="New Post").exists())

    def test_like_post(self):
        test_post_id = self.post.id
        self.assertFalse(PostLike.objects.filter(owner=self.post).exists())
        response = self.client.post(reverse('like', args=[test_post_id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PostLike.objects.filter(owner=self.post).exists())

    def test_unlike_post(self):
        test_post_id = self.post.id
        self.assertFalse(PostLike.objects.filter(owner=self.post).exists())
        response = self.client.post(reverse('like', args=[test_post_id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PostLike.objects.filter(owner=self.post).exists())
        response = self.client.post(reverse('like', args=[test_post_id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(PostLike.objects.filter(owner=self.post).exists())

    def test_add_comment(self):
        test_post_id = self.post.id
        self.assertFalse(Comment.objects.filter(post = self.post).count() > 1)
        response = self.client.post(reverse('add_comment', args=[test_post_id]), {'content': 'test comment'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Comment.objects.filter(post = self.post).count() > 1)

    def test_like_comment(self):
        self.assertFalse(CommentLike.objects.filter(owner=self.comment).exists())
        response = self.client.post(reverse('comment_like', args=[self.post.id]),)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CommentLike.objects.filter(owner=self.comment).exists())

    def test_unlike_comment(self):
        self.assertFalse(CommentLike.objects.filter(owner=self.comment).exists())
        response = self.client.post(reverse('comment_like', args=[self.post.id]), )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CommentLike.objects.filter(owner=self.comment).exists())
        response = self.client.post(reverse('comment_like', args=[self.post.id]), )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(CommentLike.objects.filter(owner=self.comment).exists())

    def test_private_post(self):
        response = self.client.get(reverse('view_post', args=[self.private_post.id]), follow=True)
        self.assertEqual(response.status_code, 403)

    def test_friends_post(self):
        response = self.client.get(reverse('view_post', args=[self.friends_post.id]), follow=True)
        self.assertEqual(response.status_code, 403)
        self.following_friend = Follow.objects.create(
            follower=self.author,
            following=self.friend_author)
        self.following_author = Follow.objects.create(
            follower=self.friend_author,
            following=self.author)
        response = self.client.get(reverse('view_post', args=[self.friends_post.id]), follow=True)

class FollowTests(TestCase):
    def setUp(self):
        self.author1 = Author.objects.create(id=1, display_name="Test Author1", description="Test Description",
                                             github="torvalds")
        self.author2 = Author.objects.create(id=2, display_name="Test Author2")
        # author 2 is following author 1 (but is not followed back)
        self.follow1 = Follow.objects.create(follower="http://darkgoldenrod/api/authors/" + str(self.author2.id),
                                             following="http://darkgoldenrod/api/authors/" + str(self.author1.id))

    def testDisplayRequest(self):
        signed_id = signing.dumps(self.author1.id)
        self.client.cookies['id'] = signed_id

        response = self.client.post(reverse('follow_requests', args=[self.author1.id]))
        self.assertContains(response, '<a href="/node/2/profile/">Test Author2</a>')
        self.assertEqual(response.status_code, 200)