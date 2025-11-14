from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Basket, BasketItem, Customer, Product


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
