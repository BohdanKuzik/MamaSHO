from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Basket, BasketItem, Customer, Order, Product


@receiver(post_save, sender=User)
def create_customer(
    sender: type[User], instance: User, created: bool, **kwargs: object
) -> None:
    if created and not instance.is_staff:
        Customer.objects.create(user=instance)


@receiver(user_logged_in)
def merge_session_basket_to_db(
    sender: type[User], request, user: User, **kwargs: object
) -> None:
    if not request:
        return

    basket_key = getattr(settings, "BASKET_SESSION_ID", "basket")
    session_basket = request.session.get(basket_key, {})

    if not session_basket:
        return

    basket_obj, _ = Basket.objects.get_or_create(user=user)

    for product_id_str, quantity in session_basket.items():
        try:
            product_id = int(product_id_str)
            product = Product.objects.get(id=product_id, available=True)

            basket_item, created = BasketItem.objects.get_or_create(
                basket=basket_obj, product=product, defaults={"quantity": 0}
            )

            if created:
                basket_item.quantity = min(quantity, product.stock)
            else:
                new_quantity = basket_item.quantity + quantity
                basket_item.quantity = min(new_quantity, product.stock)

            if basket_item.quantity > 0:
                basket_item.save()
            else:
                basket_item.delete()

        except (ValueError, Product.DoesNotExist):
            continue

    request.session[basket_key] = {}
    request.session.modified = True


_order_status_cache = {}


@receiver(pre_save, sender=Order)
def store_order_status(sender: type[Order], instance: Order, **kwargs: object) -> None:
    """Store the old status before saving to detect changes"""
    if instance.pk:
        try:
            old_order = Order.objects.get(pk=instance.pk)
            _order_status_cache[instance.pk] = old_order.status
        except Order.DoesNotExist:
            pass


@receiver(post_save, sender=Order)
def send_order_status_change_email(sender: type[Order], instance: Order, created: bool, **kwargs: object) -> None:
    """Send email to customer when order status changes"""
    if created:
        return
    
    old_status = _order_status_cache.get(instance.pk)
    
    if old_status and old_status != instance.status:
        from .order_views import send_customer_order_status_changed_email
        
        status_choices = dict(Order._meta.get_field('status').choices)
        old_status_display = status_choices.get(old_status, old_status)
        
        try:
            send_customer_order_status_changed_email(instance, old_status_display, None)
        except Exception:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(
                f"Failed to send status change email for order {instance.id}",
                exc_info=True,
            )
    
    _order_status_cache.pop(instance.pk, None)
