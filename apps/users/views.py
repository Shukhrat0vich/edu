"""
Authentication views for EduAnalytics.
Handles login, logout, and profile.
"""

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator


class LoginView(View):
    """Session-based login view."""

    template_name = "users/login.html"

    def get(self, request):

        if request.user.is_authenticated:
            return redirect("dashboard:home")

        return render(request, self.template_name)

    def post(self, request):

        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        if not email or not password:
            messages.error(request, "Please enter both email and password.")
            return render(request, self.template_name)

        user = authenticate(request, username=email, password=password)

        if user is not None:

            if not user.is_active:
                messages.error(request, "Your account has been deactivated.")
                return render(request, self.template_name)

            login(request, user)

            messages.success(request, f"Welcome back, {user.full_name}!")

            next_url = request.GET.get("next")

            if next_url:
                return redirect(next_url)

            return redirect("dashboard:home")

        messages.error(request, "Invalid email or password.")
        return render(
            request,
            self.template_name,
            {"email": email},
        )


class LogoutView(View):
    """Logout view."""

    @method_decorator(login_required)
    def post(self, request):
        logout(request)
        messages.info(request, "You have been logged out.")
        return redirect("users:login")

    @method_decorator(login_required)
    def get(self, request):
        logout(request)
        return redirect("users:login")


@method_decorator(login_required, name="dispatch")
class ProfileView(View):
    """User profile view."""

    template_name = "users/profile.html"

    def get(self, request):

        context = {
            "user": request.user
        }

        if hasattr(request.user, "student_profile"):
            context["profile"] = request.user.student_profile

        if hasattr(request.user, "teacher_profile"):
            context["profile"] = request.user.teacher_profile

        return render(request, self.template_name, context)

    def post(self, request):

        user = request.user

        full_name = request.POST.get("full_name", "").strip()

        if full_name:
            user.full_name = full_name
            user.save(update_fields=["full_name"])

        messages.success(request, "Profile updated successfully.")

        return redirect("users:profile")