from __future__ import annotations

from decimal import Decimal
from typing import Dict, Iterator

from django.conf import settings
from django.db.models import Sum
from django.http import HttpRequest

from catalog.models import Basket, BasketItem, Product


class SessionBasket:
    def __init__(self: "SessionBasket", request: HttpRequest) -> None:
        self.request = request
        self.session = request.session
        basket_key = getattr(settings, "BASKET_SESSION_ID", "basket")
        if basket_key not in self.session:
            self.session[basket_key] = {}
        self.basket = self.session[basket_key]

    def add(
        self: "SessionBasket",
        product: Product,
        quantity: int = 1,
        update_quantity: bool = False,
    ) -> None:
        product_id = str(product.id)
        basket_key = getattr(settings, "BASKET_SESSION_ID", "basket")

        if update_quantity:
            self.basket[product_id] = quantity
        else:
            current_quantity = self.basket.get(product_id, 0)
            self.basket[product_id] = current_quantity + quantity

        if self.basket[product_id] <= 0:
            self.basket.pop(product_id, None)
        else:
            if self.basket[product_id] > product.stock:
                self.basket[product_id] = product.stock

        self.session[basket_key] = self.basket
        self.session.modified = True

    def remove(self: "SessionBasket", product: Product) -> None:
        product_id = str(product.id)
        basket_key = getattr(settings, "BASKET_SESSION_ID", "basket")
        self.basket.pop(product_id, None)
        self.session[basket_key] = self.basket
        self.session.modified = True

    def __iter__(self: "SessionBasket") -> Iterator[Dict[str, object]]:
        product_ids = list(self.basket.keys())
        products = Product.objects.filter(id__in=product_ids).select_related("category")
        for product in products:
            quantity = self.basket.get(str(product.id), 0)
            if quantity > 0:
                yield {
                    "product": product,
                    "price": product.price,
                    "quantity": quantity,
                    "total_price": product.price * quantity,
                }

    def __len__(self: "SessionBasket") -> int:
        return sum(self.basket.values())

    def get_total_price(self: "SessionBasket") -> Decimal:
        total = Decimal("0.00")
        product_ids = list(self.basket.keys())
        products = Product.objects.filter(id__in=product_ids)
        for product in products:
            quantity = self.basket.get(str(product.id), 0)
            if quantity > 0:
                total += product.price * quantity
        return total

    def clear(self: "SessionBasket") -> None:
        basket_key = getattr(settings, "BASKET_SESSION_ID", "basket")
        self.session[basket_key] = {}
        self.session.modified = True
        self.basket = {}

    def get_items_dict(self: "SessionBasket") -> Dict[str, int]:
        return dict(self.basket)


class BasketView:
    def __init__(self: "BasketView", request: HttpRequest) -> None:
        if not request.user.is_authenticated:
            raise ValueError(
                "Кошик у БД доступний тільки для авторизованих користувачів"
            )
        basket_obj, _ = Basket.objects.get_or_create(user=request.user)
        self.basket = basket_obj

    def add(
        self: "BasketView",
        product: Product,
        quantity: int = 1,
        update_quantity: bool = False,
    ) -> None:
        item, _created = BasketItem.objects.get_or_create(
            basket=self.basket, product=product, defaults={"quantity": 0}
        )
        if update_quantity:
            item.quantity = quantity
        else:
            item.quantity += quantity

        if item.quantity <= 0:
            item.delete()
            return

        if item.quantity > product.stock:
            item.quantity = product.stock

        item.save()

    def remove(self: "BasketView", product: Product) -> None:
        BasketItem.objects.filter(basket=self.basket, product=product).delete()

    def __iter__(self: "BasketView") -> Iterator[Dict[str, object]]:
        items = self.basket.items.select_related("product").all()
        for item in items:
            yield {
                "product": item.product,
                "price": item.product.price,
                "quantity": item.quantity,
                "total_price": item.product.price * item.quantity,
            }

    def __len__(self: "BasketView") -> int:
        total_quantity = self.basket.items.aggregate(total=Sum("quantity"))
        return total_quantity["total"] or 0

    def get_total_price(self: "BasketView") -> Decimal:
        return sum(
            (
                item.product.price * item.quantity
                for item in self.basket.items.select_related("product")
            ),
            Decimal("0.00"),
        )

    def clear(self: "BasketView") -> None:
        self.basket.items.all().delete()
