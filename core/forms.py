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
                "placeholder": "Ваш логін",
            }
        )
        self.fields["username"].label = "Ім'я користувача"
        self.fields[
            "username"
        ].help_text = (
            "До 150 символів. Використовуйте лише літери, цифри та символи @/./+/-/_"
        )
        self.fields["password1"].widget.attrs.update(
            {
                "class": DAISY_PASSWORD,
                "placeholder": "Створіть пароль",
            }
        )
        self.fields["password1"].label = "Пароль"
        self.fields["password1"].help_text = (
            "Пароль має містити щонайменше 8 символів, не бути занадто схожим "
            "на особисту інформацію, не бути поширеним або повністю цифровим."
        )
        self.fields["password2"].widget.attrs.update(
            {
                "class": DAISY_PASSWORD,
                "placeholder": "Підтвердіть пароль",
            }
        )
        self.fields["password2"].label = "Підтвердити пароль"
        self.fields[
            "password2"
        ].help_text = "Введіть той самий пароль ще раз для підтвердження."


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {
                "class": DAISY_INPUT,
                "placeholder": "Ім'я користувача",
                "autofocus": True,
            }
        )
        self.fields["username"].label = "Ім'я користувача"
        self.fields["password"].widget.attrs.update(
            {
                "class": DAISY_PASSWORD,
                "placeholder": "Пароль",
            }
        )
        self.fields["password"].label = "Пароль"
