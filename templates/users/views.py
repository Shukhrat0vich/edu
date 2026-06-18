from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views import View


class LoginView(View):

    template_name = "users/login.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):

        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard:home")

        return render(request, self.template_name, {
            "error": "Invalid email or password"
        })