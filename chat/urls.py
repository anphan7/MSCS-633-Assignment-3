"""URL routes for the chat app."""

from django.urls import path

from chat import views

app_name = "chat"

urlpatterns = [
    path("", views.chatPage, name="page"),
    path("api/reply/", views.chatReply, name="reply"),
]
