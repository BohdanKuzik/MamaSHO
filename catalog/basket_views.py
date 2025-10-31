from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Product
from .basket import Basket


def basket_detail(request):
    basket = Basket(request)
    return render(request, "catalog/basket_detail.html", {"basket": basket})


@require_POST
def basket_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    basket = Basket(request)

    if not product.available:
        if not request.headers.get("HX-Request"):
            messages.error(request, "Цей товар недоступний для замовлення.")
        return redirect("product_detail", pk=product_id)

    quantity = int(request.POST.get("quantity", 1))

    basket_quantity = basket.basket.get(str(product_id), {}).get("quantity", 0)
    if basket_quantity + quantity > product.stock:
        messages.warning(
            request,
            f"Доступно тільки {product.stock} шт. на складі. Додано {product.stock - basket_quantity} шт.",
        )
        quantity = max(0, product.stock - basket_quantity)

    if quantity > 0:
        basket.add(product, quantity=quantity, update_quantity=False)
        if not request.headers.get("HX-Request"):
            messages.success(request, f'Товар "{product.name}" додано до корзини!')
    else:
        if not request.headers.get("HX-Request"):
            messages.warning(
                request, "Неможливо додати більше товару - недостатньо на складі."
            )

    if request.headers.get("HX-Request") == "true":
        messages.success(request, f'Товар "{product.name}" додано до корзини!')
        return render(request, "catalog/partials/basket_count.html", {"basket": basket})

    # Иначе редирект обратно
    return redirect("product_detail", pk=product_id)


@require_POST
def basket_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    basket = Basket(request)
    basket.remove(product)
    messages.success(request, f'Товар "{product.name}" видалено з корзини!')

    if request.headers.get("HX-Request") == "true":
        return render(
            request, "catalog/partials/basket_content.html", {"basket": basket}
        )

    return redirect("basket_detail")


@require_POST
def basket_update(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    basket = Basket(request)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
        quantity = 1

    if quantity > product.stock:
        messages.warning(request, f"Доступно тільки {product.stock} шт. на складі.")
        quantity = product.stock

    if quantity > 0:
        basket.add(product, quantity=quantity, update_quantity=True)
        messages.success(request, f'Кількість товару "{product.name}" оновлено!')
    else:
        basket.remove(product)
        messages.success(request, f'Товар "{product.name}" видалено з корзини!')

    if request.headers.get("HX-Request") == "true":
        return render(
            request, "catalog/partials/basket_content.html", {"basket": basket}
        )

    return redirect("basket_detail")


@require_POST
def basket_clear(request):
    basket = Basket(request)
    basket.clear()

    if request.headers.get("HX-Request") == "true":
        return render(
            request, "catalog/partials/basket_content.html", {"basket": basket}
        )

    if not request.headers.get("HX-Request"):
        messages.success(request, "Корзину очищено!")

    return redirect("basket_detail")
