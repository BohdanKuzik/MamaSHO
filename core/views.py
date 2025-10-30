from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse
from .forms import SignupForm, LoginForm


def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse("product_list"))
    else:
        form = SignupForm()

    return render(request, "registration/signup.html", {"form": form})


class CustomLoginView(LoginView):
    authentication_form = LoginForm
    template_name = "registration/login.html"
