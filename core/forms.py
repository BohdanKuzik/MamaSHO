from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


DAISY_INPUT = "input input-bordered w-full"
DAISY_PASSWORD = "input input-bordered w-full"
DAISY_CHECKBOX = "checkbox"


class SignupForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {
                "class": DAISY_INPUT,
                "placeholder": "Your username",
            }
        )
        self.fields["password1"].widget.attrs.update(
            {
                "class": DAISY_PASSWORD,
                "placeholder": "Create password",
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                "class": DAISY_PASSWORD,
                "placeholder": "Confirm password",
            }
        )


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {
                "class": DAISY_INPUT,
                "placeholder": "Username",
                "autofocus": True,
            }
        )
        self.fields["password"].widget.attrs.update(
            {
                "class": DAISY_PASSWORD,
                "placeholder": "Password",
            }
        )
