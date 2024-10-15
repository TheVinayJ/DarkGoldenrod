from django.urls import path
from . import views, login

urlpatterns = [
    path("", views.index, name="index"),
    path("add/", views.editor, name="add"),
    path("save/", views.save, name="save"),
    path("posts/<int:post_id>/", views.view_post, name="view_post"),
    path('authors/', views.AuthorListView.as_view(), name='authors'),
    path('authors/follow/<int:author_id>/', views.follow_author, name='follow_author'),  # New URL for follow action
    ### SUGGESTION: Maybe we should change the profile path to authors/<int:user_id>/profile/
    path('<int:user_id>/profile/', views.profile, name='profile'),
    path('login/', login.login, name='login'),
    path('signup/', login.signup, name='signup'),
    path('authors/unfollow/<int:author_id>/', views.unfollow_author, name='unfollow_author'),
    path('feed/', views.display_feed, name='following_feed'),

]