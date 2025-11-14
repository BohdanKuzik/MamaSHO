from __future__ import annotations

import logging

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .basket import BasketView, SessionBasket
from .models import Product


logger = logging.getLogger(__name__)


def get_basket(request: HttpRequest) -> BasketView | SessionBasket:
    if request.user.is_authenticated:
        return BasketView(request)
    return SessionBasket(request)


def basket_detail(request: HttpRequest) -> HttpResponse:
    basket = get_basket(request)
    return render(request, "catalog/basket_detail.html", {"basket": basket})


@require_POST
def basket_add(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(Product, id=product_id)
    basket = get_basket(request)

    if not product.available:
        user_id = request.user.id if request.user.is_authenticated else None
        logger.warning(
            "Attempt to add unavailable product",
            extra={"product_id": product_id, "user_id": user_id},
        )
        return redirect("product_detail", pk=product_id)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    is_htmx = request.headers.get("HX-Request") == "true"

    if request.user.is_authenticated:
        existing_item = basket.basket.items.filter(product=product).first()
        basket_quantity = existing_item.quantity if existing_item else 0
    else:
        basket_quantity = basket.basket.get(str(product.id), 0)

    if basket_quantity + quantity > product.stock:
        allowed_to_add = max(0, product.stock - basket_quantity)
        if allowed_to_add == 0:
            user_id = request.user.id if request.user.is_authenticated else None
            logger.info(
                "Basket add blocked: insufficient stock",
                extra={
                    "product_id": product_id,
                    "user_id": user_id,
                    "requested": quantity,
                    "available_to_add": allowed_to_add,
                },
            )
            if is_htmx:
                return render(
                    request,
                    "catalog/partials/basket_count.html",
                    {"basket": basket},
                )
            return redirect("product_detail", pk=product_id)

        user_id = request.user.id if request.user.is_authenticated else None
        logger.info(
            "Basket add limited by stock",
            extra={
                "product_id": product_id,
                "user_id": user_id,
                "requested": quantity,
                "added": allowed_to_add,
            },
        )
        quantity = allowed_to_add

    if quantity > 0:
        basket.add(product, quantity=quantity, update_quantity=False)
        user_id = request.user.id if request.user.is_authenticated else None
        logger.info(
            "Product added to basket",
            extra={
                "product_id": product_id,
                "user_id": user_id,
                "quantity": quantity,
            },
        )
    else:
        user_id = request.user.id if request.user.is_authenticated else None
        logger.info(
            "Basket add skipped: insufficient stock",
            extra={
                "product_id": product_id,
                "user_id": user_id,
                "basket_quantity": basket_quantity,
            },
        )

    if is_htmx:
        return render(request, "catalog/partials/basket_count.html", {"basket": basket})

    return redirect("product_detail", pk=product_id)


@require_POST
def basket_remove(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(Product, id=product_id)
    basket = get_basket(request)
    basket.remove(product)
    user_id = request.user.id if request.user.is_authenticated else None
    logger.info(
        "Product removed from basket",
        extra={
            "product_id": product_id,
            "user_id": user_id,
        },
    )

    if request.headers.get("HX-Request") == "true":
        return render(
            request, "catalog/partials/basket_content.html", {"basket": basket}
        )

    if request.user.is_authenticated:
        return redirect("basket_detail")
    return redirect("product_list")


@require_POST
def basket_update(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(Product, id=product_id)
    basket = get_basket(request)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
        quantity = 1

    if quantity > product.stock:
        user_id = request.user.id if request.user.is_authenticated else None
        logger.info(
            "Basket update limited by stock",
            extra={
                "product_id": product_id,
                "user_id": user_id,
                "requested": quantity,
                "stock": product.stock,
            },
        )
        quantity = product.stock

    user_id = request.user.id if request.user.is_authenticated else None
    if quantity > 0:
        basket.add(product, quantity=quantity, update_quantity=True)
        logger.info(
            "Basket quantity updated",
            extra={
                "product_id": product_id,
                "user_id": user_id,
                "quantity": quantity,
            },
        )
    else:
        basket.remove(product)
        logger.info(
            "Product removed from basket due to zero quantity",
            extra={
                "product_id": product_id,
                "user_id": user_id,
            },
        )

    if request.headers.get("HX-Request") == "true":
        return render(
            request, "catalog/partials/basket_content.html", {"basket": basket}
        )

    if request.user.is_authenticated:
        return redirect("basket_detail")
    return redirect("product_list")


@require_POST
def basket_clear(request: HttpRequest) -> HttpResponse:
    basket = get_basket(request)
    basket.clear()
    user_id = request.user.id if request.user.is_authenticated else None
    logger.info("Basket cleared", extra={"user_id": user_id})

    if request.headers.get("HX-Request") == "true":
        return render(
            request, "catalog/partials/basket_content.html", {"basket": basket}
        )

    if request.user.is_authenticated:
        return redirect("basket_detail")
    return redirect("product_list")
