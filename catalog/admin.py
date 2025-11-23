from django.contrib import admin

from .models import (
    Category,
    Customer,
    Order,
    OrderItem,
    Product,
    ProductReservation,
    Size,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ("get_value_display", "order")
    list_editable = ("order",)
    ordering = ("order", "value")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "available")
    list_filter = ("category", "available")
    search_fields = ("name",)
    list_editable = ("price", "stock", "available")


@admin.register(ProductReservation)
class ProductReservationAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "user",
        "session_key",
        "quantity",
        "reserved_at",
        "expires_at",
    )
    list_filter = ("reserved_at", "expires_at")
    search_fields = ("product__name", "user__username")
    readonly_fields = ("reserved_at", "expires_at")
    date_hierarchy = "reserved_at"


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("get_first_name", "get_last_name", "get_email", "phone")
    search_fields = ("user__first_name", "user__last_name", "user__email")

    def get_first_name(self: "CustomerAdmin", obj: Customer) -> str:
        return obj.user.first_name

    get_first_name.short_description = "First Name"

    def get_last_name(self: "CustomerAdmin", obj: Customer) -> str:
        return obj.user.last_name

    get_last_name.short_description = "Last Name"

    def get_email(self: "CustomerAdmin", obj: Customer) -> str:
        return obj.user.email

    get_email.short_description = "Email"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer",
        "total_price",
        "payment_method",
        "payment_status",
        "delivery_city",
        "delivery_region",
        "status",
        "created_at",
    )
    list_filter = (
        "status",
        "payment_status",
        "payment_method",
        "created_at",
        "delivery_region",
    )
    search_fields = (
        "id",
        "customer__user__first_name",
        "customer__user__last_name",
        "customer__user__email",
        "email",
        "delivery_city",
        "delivery_phone",
    )
    readonly_fields = ("created_at", "total_price")
    fieldsets = (
        (
            "Основна інформація",
            {
                "fields": (
                    "customer",
                    "status",
                    "total_price",
                    "payment_method",
                    "payment_status",
                    "paid_at",
                    "created_at",
                )
            },
        ),
        (
            "Дані доставки",
            {
                "fields": (
                    "delivery_region",
                    "delivery_city",
                    "delivery_address",
                    "delivery_postal_code",
                    "delivery_phone",
                    "email",
                    "comment",
                )
            },
        ),
    )
    inlines = [OrderItemInline]
    list_editable = ("status",)
    date_hierarchy = "created_at"
