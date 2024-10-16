from django.urls import path
from . import views, login

urlpatterns = [
    path("", views.index, name="index"),
    path("add/", views.editor, name="add"),
    path("save/", views.save, name="save"),
    path("posts/<int:post_id>/", views.view_post, name="view_post"),
    path('authors/', views.AuthorListView.as_view(), name='authors'),
    path('<int:user_id>/profile/', views.profile, name='profile'),
    path('login/', login.login, name='login'),
    path('signup/', login.signup, name='signup'),
    path('images/', views.upload_image, name='images'),
]