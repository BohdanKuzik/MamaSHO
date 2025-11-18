from django import forms
from .models import Order, Product

UKRAINIAN_REGIONS = [
    ("", "Оберіть область"),
    ("Вінницька", "Вінницька"),
    ("Волинська", "Волинська"),
    ("Дніпропетровська", "Дніпропетровська"),
    ("Донецька", "Донецька"),
    ("Житомирська", "Житомирська"),
    ("Закарпатська", "Закарпатська"),
    ("Запорізька", "Запорізька"),
    ("Івано-Франківська", "Івано-Франківська"),
    ("Київська", "Київська"),
    ("Кіровоградська", "Кіровоградська"),
    ("Луганська", "Луганська"),
    ("Львівська", "Львівська"),
    ("Миколаївська", "Миколаївська"),
    ("Одеська", "Одеська"),
    ("Полтавська", "Полтавська"),
    ("Рівненська", "Рівненська"),
    ("Сумська", "Сумська"),
    ("Тернопільська", "Тернопільська"),
    ("Харківська", "Харківська"),
    ("Херсонська", "Херсонська"),
    ("Хмельницька", "Хмельницька"),
    ("Черкаська", "Черкаська"),
    ("Чернівецька", "Чернівецька"),
    ("Чернігівська", "Чернігівська"),
]


class CreateProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ["image"]


class UpdateProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"


class OrderForm(forms.ModelForm):
    delivery_region = forms.ChoiceField(
        choices=UKRAINIAN_REGIONS,
        label="Область",
        required=True,
        widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
    )
    delivery_city = forms.CharField(
        label="Місто",
        max_length=100,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "input input-bordered w-full",
                "placeholder": "Наприклад: Київ",
            }
        ),
    )
    delivery_address = forms.CharField(
        label="Адреса доставки",
        required=True,
        widget=forms.Textarea(
            attrs={
                "class": "textarea textarea-bordered w-full",
                "placeholder": "Вулиця, будинок, квартира",
                "rows": 3,
            }
        ),
    )
    delivery_postal_code = forms.CharField(
        label="Поштовий індекс",
        max_length=10,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "input input-bordered w-full",
                "placeholder": "Наприклад: 01001",
            }
        ),
    )
    delivery_phone = forms.CharField(
        label="Телефон для доставки",
        max_length=20,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "input input-bordered w-full",
                "placeholder": "+380501234567",
            }
        ),
        help_text="Формат: +380501234567",
    )
    email = forms.EmailField(
        label="Email для повідомлень",
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "input input-bordered w-full",
                "placeholder": "example@email.com",
            }
        ),
        help_text="На цей email будуть надсилатися повідомлення про статус замовлення",
    )
    comment = forms.CharField(
        label="Коментар до замовлення",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "textarea textarea-bordered w-full",
                "placeholder": "Додаткові побажання щодо доставки (необов'язково)",
                "rows": 3,
            }
        ),
    )
    payment_method = forms.ChoiceField(
        label="Спосіб оплати",
        choices=[
            ("cash_on_delivery", "Накладений платіж (оплата при отриманні)"),
            ("card_online", "Онлайн оплата карткою"),
        ],
        widget=forms.RadioSelect(attrs={"class": "radio"}),
        initial="cash_on_delivery",
    )

    class Meta:
        model = Order
        fields = [
            "delivery_region",
            "delivery_city",
            "delivery_address",
            "delivery_postal_code",
            "delivery_phone",
            "email",
            "payment_method",
            "comment",
        ]

    def clean_delivery_phone(self):
        phone = self.cleaned_data.get("delivery_phone")
        if phone and not phone.startswith("+380"):
            raise forms.ValidationError(
                "Номер телефону повинен починатися з +380 (український формат)"
            )
        return phone
