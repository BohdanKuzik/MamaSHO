from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.contrib.auth import login, authenticate
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import SignupForm, LoginForm


def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            authenticated_user = authenticate(
                request, username=username, password=raw_password
            )
            if authenticated_user is not None:
                login(request, authenticated_user)
            return redirect(reverse("product_list"))
    else:
        form = SignupForm()

    return render(request, "registration/signup.html", {"form": form})


class CustomLoginView(LoginView):
    authentication_form = LoginForm
    template_name = "registration/login.html"


def robots_txt(request):
    site_url = getattr(settings, "SITE_URL", "https://mamasho.store").rstrip("/")
    lines = [
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {site_url}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
