from django.urls import path, include
from . import views, login
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from rest_framework_simplejwt.views import TokenRefreshView
from .login import SignupView, LoginView, LogoutView, UserInfoView

urlpatterns = [
    path("", views.display_feed, name="index"),
    path("add/", views.editor, name="add"),
    path("posts/<int:post_id>/", views.view_post, name="view_post"),
    path("posts/<int:id>/like/", views.post_like, name="like"),
    path("posts/<int:id>/likecomment/", views.comment_like, name="comment_like"),
    path('posts/<int:id>/add_comment/', views.add_comment, name="add_comment"),
    path('authors/', views.authors_list, name='authors'),
    path('authors/follow/<int:author_id>/', views.local_api_follow, name='follow_author'),  # New URL for follow action
    path('authors/unfollow/<int:author_id>/', views.unfollow_author, name='unfollow_author'),
    ### SUGGESTION: Maybe we should change the profile path to authors/<int:user_id>/profile/
    path("<int:author_id>/profile/", views.profile, name='profile'),
    path("<int:author_id>/followers/", views.followers_following, name='followers'),
    path("<int:author_id>/followings/", views.followers_following, name='followings'),

    path('<int:author_id>/follower_requests/', views.follow_requests, name='follow_requests'),
    path('<int:author_id>/follower_requests/approve/<int:follower_id>/', views.approve_follow, name='approve_follow'),
    path('<int:author_id>/follower_requests/decline/<int:follower_id>/', views.decline_follow, name='decline_follow'),

    path("<int:author_id>/profile/edit", views.edit_profile, name='profile_edit'),
    path("<int:author_id>/profile/edit/save", views.edit_profile, name='profile_edit_save'),
    path('upload-avatar/', views.edit_profile, name='upload_avatar'),
    path('login/', login.login, name='login'),
    path('signup/', login.signup, name='signup'),
    path('images/', views.upload_image, name='images'),
    path('feed/', views.display_feed, name='following_feed'),
    path("posts/<int:id>/repost/", views.repost_post, name="repost"),
    path('signout/', login.signout, name='signout'),
    path("posts/<int:post_id>/edit/", views.edit_post, name="edit_post"),
    path("posts/<int:post_id>/delete/", views.delete_post, name="delete_post"),

    # API
    path('api/authors/<int:author_id>/inbox/', views.inbox, name='inbox'),
    path('api/authors/', views.api_authors_list, name='api_authors_list'),    
    path('api/signup/', SignupView.as_view(), name='api_signup'),
    path('api/login/', LoginView.as_view(), name='api_login'),
    path('api/logout/', LogoutView.as_view(), name='api_logout'),
    path('api/user-info/', UserInfoView.as_view(), name='user_info'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/authors/<int:author_id>/posts', views.author_posts, name='author_posts'),
]