from __future__ import annotations

from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self: "Category") -> str:
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self: "Product") -> str:
        return self.name

    class Meta:
        ordering = ("-created_at",)


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="products/")
    order = models.PositiveIntegerField(default=0, help_text="Порядок відображення")

    class Meta:
        ordering = ["order", "id"]

    def __str__(self: "ProductImage") -> str:
        return f"Image {self.id} for {self.product.name}"


phone_validator = RegexValidator(
    regex=r"^\+?1?\d{9,15}$",
    message="Номер телефону повинен бути в форматі: '+380501234567'. До 15 цифр.",
)


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(
        max_length=20, blank=True, null=True, validators=[phone_validator]
    )
    address = models.TextField(blank=True, null=True)

    def __str__(self: "Customer") -> str:
        return f"{self.user.first_name} {self.user.last_name} ({self.user.username})"


class Order(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="orders"
    )
    products = models.ManyToManyField(Product, through="OrderItem")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("shipped", "Shipped"),
            ("delivered", "Delivered"),
        ],
        default="pending",
    )

    def __str__(self: "Order") -> str:
        return f"Order #{self.id} by {self.customer}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self: "OrderItem") -> str:
        return f"{self.quantity} x {self.product.name}"


class Basket(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="basket")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_total_price(self: "Basket") -> Decimal:
        return sum((item.get_total() for item in self.items.all()), Decimal("0"))

    def get_total_quantity(self: "Basket") -> int:
        return sum(item.quantity for item in self.items.all())

    def __str__(self: "Basket") -> str:
        return f"Basket for {self.user}"


class BasketItem(models.Model):
    basket = models.ForeignKey(Basket, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("basket", "product")

    def __str__(self: "BasketItem") -> str:
        return f"{self.product} in {self.basket}"

    def get_total_price(self: "BasketItem") -> Decimal:
        return self.product.price * self.quantity
