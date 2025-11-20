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


class Size(models.Model):
    """Модель для розмірів (зросту) продуктів"""
    HEIGHT_CHOICES = [
        ("74-84", "74-84 см"),
        ("84-94", "84-94 см"),
        ("94-104", "94-104 см"),
        ("104-114", "104-114 см"),
        ("114-124", "114-124 см"),
        ("124-134", "124-134 см"),
        ("134-144", "134-144 см"),
        ("144-154", "144-154 см"),
        ("154-160", "154-160 см"),
        ("160+", "160+ см"),
    ]
    
    value = models.CharField(
        max_length=10,
        choices=HEIGHT_CHOICES,
        unique=True,
        verbose_name="Зріст (см)"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Порядок відображення (менше = вище)"
    )

    class Meta:
        ordering = ["order", "value"]
        verbose_name = "Size"
        verbose_name_plural = "Sizes"

    def __str__(self: "Size") -> str:
        return self.get_value_display()


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
    sizes = models.ManyToManyField(
        "Size",
        blank=True,
        related_name="products",
        verbose_name="Розміри (зріст)"
    )
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
    regex=r"^\+380\d{9}$",
    message="Номер телефону повинен бути в форматі: '+380501234567' (12 цифр після +).",
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
            ("pending", "Очікує обробки"),
            ("processing", "В обробці"),
            ("shipped", "Відправлено"),
            ("delivered", "Доставлено"),
            ("cancelled", "Скасовано"),
        ],
        default="pending",
    )
    payment_method = models.CharField(
        max_length=50,
        choices=[
            ("cash_on_delivery", "Накладений платіж (оплата при отриманні)"),
            ("card_online", "Онлайн оплата карткою"),
        ],
        default="cash_on_delivery",
        verbose_name="Спосіб оплати",
    )
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Очікує оплати"),
            ("paid", "Оплачено"),
            ("failed", "Помилка оплати"),
            ("refunded", "Повернено"),
        ],
        default="pending",
        verbose_name="Статус оплати",
    )
    paid_at = models.DateTimeField(blank=True, null=True, verbose_name="Дата оплати")
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Загальна сума замовлення", default=0
    )
    delivery_address = models.TextField(verbose_name="Адреса доставки", blank=True, null=True)
    delivery_city = models.CharField(max_length=100, verbose_name="Місто", blank=True, null=True)
    delivery_region = models.CharField(max_length=100, verbose_name="Область", blank=True, null=True)
    delivery_postal_code = models.CharField(
        max_length=10, blank=True, null=True, verbose_name="Поштовий індекс"
    )
    delivery_phone = models.CharField(
        max_length=20,
        validators=[phone_validator],
        verbose_name="Телефон для доставки",
        blank=True,
        null=True,
    )
    email = models.EmailField(
        verbose_name="Email для повідомлень",
        help_text="Email для отримання повідомлень про статус замовлення",
        blank=True,
        null=True,
    )
    comment = models.TextField(blank=True, null=True, verbose_name="Коментар до замовлення")

    class Meta:
        ordering = ("-created_at",)

    def __str__(self: "Order") -> str:
        return f"Замовлення #{self.id} від {self.customer}"

    def get_total_price(self: "Order") -> Decimal:
        return sum(
            (item.product.price * item.quantity for item in self.items.all()),
            Decimal("0.00"),
        )

    def can_be_cancelled(self: "Order") -> bool:
        return self.status in ("pending", "processing")

    def cancel(self: "Order") -> None:
        if not self.can_be_cancelled():
            raise ValueError("Замовлення не може бути скасоване в поточному статусі")
        
        self.status = "cancelled"
        self.save()
        
        for item in self.items.all():
            item.product.stock += item.quantity
            item.product.save()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self: "OrderItem") -> str:
        return f"{self.quantity} x {self.product.name}"

    def get_total_price(self: "OrderItem") -> Decimal:
        """Повертає загальну ціну позиції замовлення"""
        return self.product.price * self.quantity


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
