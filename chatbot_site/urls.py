"""URL configuration for the chatbot_site project.

Routes the site root at the `chat` app; `/admin/` remains Django's admin.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("chat.urls")),
    path("admin/", admin.site.urls),
]
