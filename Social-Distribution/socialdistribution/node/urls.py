from django.urls import path, include
from . import views, login
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from rest_framework_simplejwt.views import TokenRefreshView
from .login import SignupView, LoginView, LogoutView, UserInfoView


urlpatterns = [
    path("", views.display_feed, name="index"),
    path("node/", views.display_feed, name="index"),
    
    path("node/add/", views.editor, name="add"),
    path("node/posts/<int:post_id>/", views.view_post, name="view_post"),
    path("node/posts/<int:id>/like/", views.local_api_like, name="like"),
    path("node/posts/<int:id>/likecomment/", views.local_api_like_comment, name="comment_like"),
    path('node/posts/<int:id>/add_comment/', views.add_comment, name="add_comment"),
    path('node/authors/', views.authors_list, name='authors'),
    path('node/authors/follow/<int:author_id>/', views.local_api_follow, name='follow_author'),  # New URL for follow action
    path('node/authors/unfollow/<int:author_id>/', views.unfollow_author, name='unfollow_author'),

    path("node/authors/<int:author_id>/followers/", views.followers_following_friends, name='followers'),
    path("node/authors/<int:author_id>/followings/", views.followers_following_friends, name='followings'),
    path("node/authors/<int:author_id>/friends/", views.followers_following_friends, name='friends'),

    path('node/authors/<int:author_id>/follower_requests/', views.follow_requests, name='follow_requests'),
    # path('node/authors/<int:author_id>/follower_requests/approve/<int:follower_id>/', views.approve_follow, name='approve_follow'),
    path('node/authors/<int:author_id>/follower_requests/decline/<int:follower_id>/', views.decline_follow, name='decline_follow'),

    path("node/authors/<int:author_id>/profile/", views.profile, name='profile'),
    path("node/authors/<int:author_id>/profile/edit", views.edit_profile, name='profile_edit'),

    path('node/upload-avatar/', views.edit_profile, name='upload_avatar'),
    path('node/login/', login.login, name='login'),
    path('node/signup/', login.signup, name='signup'),
    path('node/images/', views.upload_image, name='images'),
    path('node/feed/', views.display_feed, name='following_feed'),
    path("node/posts/<int:id>/repost/", views.repost_post, name="repost"),
    path('node/signout/', login.signout, name='signout'),
    path("node/posts/<int:post_id>/edit/", views.edit_post, name="edit_post"),
    path("node/posts/<int:post_id>/delete/", views.delete_post, name="delete_post"),
    path('node/authors/<int:author_id>/posts', views.author_posts, name='author_posts'),
    path('node/authors/<int:author_id>/posts/<int:post_id>', views.api_get_post_from_author, name='api_get_post_from_author'),

    # API
    path('api/authors/<int:author_id>/inbox/', views.inbox, name='inbox'),
    path('api/authors/<int:author_id>/inbox', views.inbox, name='inbox'),
    
    path('api/authors/', views.api_authors_list, name='api_authors_list'),
    
    path('api/signup/', SignupView.as_view(), name='api_signup'),
    path('api/login/', LoginView.as_view(), name='api_login'),
    path('api/logout/', LogoutView.as_view(), name='api_logout'),
    path('api/user-info/', UserInfoView.as_view(), name='user_info'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('api/posts/<int:post_id>', views.get_post, name='get_post'),
    path('api/authors/<int:author_id>/posts', views.author_posts, name='author_posts'),
    path('api/authors/<int:author_id>/posts/<int:post_id>', views.api_get_post_from_author, name='api_get_post_from_author'),
    path('api/authors/<int:author_id>/posts/<int:post_id>/likes', views.get_post_likes, name='get_post_likes'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),    
    path('api/posts/<str:post_url>/likes/', views.get_post_likes_by_id, name='post_likes_by_id'),
    path('api/authors/<str:author_id>/posts/<str:post_id>/comments/<str:comment_id>/likes/', views.get_comment_likes, name='get_comment_likes'),
    path('api/posts/<str:post_url>/comments', views.get_comments_from_post, name='get_comments_from_post'),
    path('api/authors/<int:author_id>/posts/<int:post_id>/comments', views.get_comments, name='get_comments'),
    path('api/authors/<int:author_id>/commented/<int:comment_id>', views.get_comment, name='get_comment'),
    path('api/authors/<int:author_id>/followers', views.followers_view, name='list_all_followers'),
    path('api/authors/<int:author_id>/followers/', views.followers_view, name='list_all_followers'),
    path('api/authors/<int:author_id>/followers/<path:follower_id>', views.followers_view, name='list_follower'),
    path('api/authors/<int:author_id>/followers/approve', views.followers_view, name='approve_follow'),
    path("api/authors/<int:author_id>/", views.api_single_author, name='single_author'),
    path("api/authors/<int:author_id>", views.api_single_author, name='single_author'),
    path("api/authors/<str:host>/api/authors/<int:author_id>", views.api_single_author, name='single_author'),
    path("api/authors/<str:host>/api/authors/<int:author_id>/", views.api_single_author, name='single_author'),
    path("api/authors/<path:author_fqid>/", views.api_single_author_fqid, name='single_author'),
    path("api/authors/<path:author_fqid>", views.api_single_author_fqid, name='single_author'),
    path("api/authors/<int:author_id>/liked", views.likes_by_author, name='likes_by_author'),
    path('api/authors/<int:author_id>/liked/<int:like_id>', views.get_like, name='get_like'),
    path('api/authors/<str:author_fqid>/liked/', views.get_author_likes_by_id, name='liked_by_author_fqid'),
    path('api/liked/<path:like_id>', views.get_like_by_id, name='get_like'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)