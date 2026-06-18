"""URL configuration for users app."""

from django.urls import path
from .views import LoginView, LogoutView, ProfileView

app_name = "users"

urlpatterns = [

    # Login
    path("login/", LoginView.as_view(), name="login"),

    # Logout
    path("logout/", LogoutView.as_view(), name="logout"),

    # Profile
    path("profile/", ProfileView.as_view(), name="profile"),

]