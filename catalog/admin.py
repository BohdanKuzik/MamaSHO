from django.contrib import admin
from .models import Category, Product, Customer, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "available")
    list_filter = ("category", "available")
    search_fields = ("name",)
    list_editable = ("price", "stock", "available")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("get_first_name", "get_last_name", "get_email", "phone")
    search_fields = ("user__first_name", "user__last_name", "user__email")

    def get_first_name(self, obj):
        return obj.user.first_name

    get_first_name.short_description = "First Name"

    def get_last_name(self, obj):
        return obj.user.last_name

    get_last_name.short_description = "Last Name"

    def get_email(self, obj):
        return obj.user.email

    get_email.short_description = "Email"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "created_at", "status")
    list_filter = ("status", "created_at")
    search_fields = (
        "customer__user__first_name",
        "customer__user__last_name",
        "customer__user__email",
    )
    inlines = [OrderItemInline]
