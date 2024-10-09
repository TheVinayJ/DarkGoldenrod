from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    # path("add/", views.editor, name="add"),
    path("posts/<int:post_id>/", views.view_post, name="view_post"),
]