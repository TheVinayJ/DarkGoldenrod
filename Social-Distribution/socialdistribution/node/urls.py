from django.urls import path
from . import views, login
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.display_feed, name="index"),
    path("add/", views.editor, name="add"),
    path("save/", views.save, name="save"),
    path("posts/<int:post_id>/", views.view_post, name="view_post"),
    path("posts/<int:id>/like/", views.post_like, name="like"),
    path('posts/<int:id>/add_comment/', views.add_comment, name="add_comment"),
    path('authors/', views.AuthorListView.as_view(), name='authors'),
    path('authors/follow/<int:author_id>/', views.follow_author, name='follow_author'),  # New URL for follow action
    path('authors/unfollow/<int:author_id>/', views.unfollow_author, name='unfollow_author'),
    ### SUGGESTION: Maybe we should change the profile path to authors/<int:user_id>/profile/
    path("<int:author_id>/profile/", views.profile, name='profile'),
    path("<int:author_id>/followers/", views.followers, name='followers'),
    # path("<int:author_id>/followings/", views.following, name='followings'),
    path("<int:author_id>/profile/edit", views.edit_profile, name='profile_edit'),
    path("<int:author_id>/profile/edit/save", views.edit_profile, name='profile_edit_save'),
    path('upload-avatar/', views.edit_profile, name='upload_avatar'),
    path('login/', login.login, name='login'),
    path('signup/', login.signup, name='signup'),
    path('images/', views.upload_image, name='images'),
    path('feed/', views.display_feed, name='following_feed'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
