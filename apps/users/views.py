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
        action = request.POST.get("action", "profile")

        if action == "password":
            current = request.POST.get("current_password", "")
            new_pw  = request.POST.get("new_password", "")
            confirm = request.POST.get("confirm_password", "")

            if not user.check_password(current):
                messages.error(request, "Current password is incorrect.")
                return redirect("users:profile")
            if len(new_pw) < 6:
                messages.error(request, "New password must be at least 6 characters.")
                return redirect("users:profile")
            if new_pw != confirm:
                messages.error(request, "New passwords do not match.")
                return redirect("users:profile")

            user.set_password(new_pw)
            user.save()
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            messages.success(request, "Password changed successfully.")
            return redirect("users:profile")

        # Default: update profile info
        full_name = request.POST.get("full_name", "").strip()
        if full_name:
            user.full_name = full_name
            user.save(update_fields=["full_name"])
        messages.success(request, "Profile updated successfully.")
        return redirect("users:profile")