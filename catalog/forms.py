from django import forms
from .models import Product


class CreateProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ["image"]


class UpdateProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"
