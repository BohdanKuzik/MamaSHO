from __future__ import annotations

from decimal import Decimal
from typing import Dict, Iterator

from django.db.models import Sum
from django.http import HttpRequest

from catalog.models import Basket, BasketItem, Product


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
