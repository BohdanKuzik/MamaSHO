from decimal import Decimal

from django.db.models import Sum

from catalog.models import Basket, BasketItem


class BasketView:
    def __init__(self, request):
        if not request.user.is_authenticated:
            raise ValueError("Кошик у БД доступний тільки для авторизованих користувачів")
        basket_obj, _ = Basket.objects.get_or_create(user=request.user)
        self.basket = basket_obj

    def add(self, product, quantity=1, update_quantity=False):
        item, created = BasketItem.objects.get_or_create(
            basket=self.basket,
            product=product,
            defaults={"quantity": 0}
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

    def remove(self, product):
        BasketItem.objects.filter(basket=self.basket, product=product).delete()

    def __iter__(self):
        items = self.basket.items.select_related("product").all()
        for item in items:
            yield {
                "product": item.product,
                "price": item.product.price,
                "quantity": item.quantity,
                "total_price": item.product.price * item.quantity,
            }

    def __len__(self):
        total_quantity = self.basket.items.aggregate(total=Sum("quantity"))
        return total_quantity["total"] or 0

    def get_total_price(self):
        return sum(
            (
                item.product.price * item.quantity
                for item in self.basket.items.select_related("product")
            ),
            Decimal("0.00"),
        )

    def clear(self):
        self.basket.items.all().delete()
