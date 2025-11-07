from __future__ import annotations

import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .basket import BasketView
from .models import Product


logger = logging.getLogger(__name__)


@login_required
def basket_detail(request: HttpRequest) -> HttpResponse:
    basket = BasketView(request)
    return render(request, "catalog/basket_detail.html", {"basket": basket})


@require_POST
@login_required
def basket_add(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(Product, id=product_id)
    basket = BasketView(request)

    if not product.available:
        logger.warning(
            "Attempt to add unavailable product",
            extra={"product_id": product_id, "user_id": request.user.id},
        )
        return redirect("product_detail", pk=product_id)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    is_htmx = request.headers.get("HX-Request") == "true"

    existing_item = basket.basket.items.filter(product=product).first()
    basket_quantity = existing_item.quantity if existing_item else 0

    if basket_quantity + quantity > product.stock:
        allowed_to_add = max(0, product.stock - basket_quantity)
        if allowed_to_add == 0:
            logger.info(
                "Basket add blocked: insufficient stock",
                extra={
                    "product_id": product_id,
                    "user_id": request.user.id,
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

        logger.info(
            "Basket add limited by stock",
            extra={
                "product_id": product_id,
                "user_id": request.user.id,
                "requested": quantity,
                "added": allowed_to_add,
            },
        )
        quantity = allowed_to_add

    if quantity > 0:
        basket.add(product, quantity=quantity, update_quantity=False)
        logger.info(
            "Product added to basket",
            extra={
                "product_id": product_id,
                "user_id": request.user.id,
                "quantity": quantity,
            },
        )
    else:
        logger.info(
            "Basket add skipped: insufficient stock",
            extra={
                "product_id": product_id,
                "user_id": request.user.id,
                "basket_quantity": basket_quantity,
            },
        )

    if is_htmx:
        return render(request, "catalog/partials/basket_count.html", {"basket": basket})

    return redirect("product_detail", pk=product_id)


@require_POST
@login_required
def basket_remove(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(Product, id=product_id)
    basket = BasketView(request)
    basket.remove(product)
    logger.info(
        "Product removed from basket",
        extra={
            "product_id": product_id,
            "user_id": request.user.id,
        },
    )

    if request.headers.get("HX-Request") == "true":
        return render(
            request, "catalog/partials/basket_content.html", {"basket": basket}
        )

    return redirect("basket_detail")


@require_POST
@login_required
def basket_update(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(Product, id=product_id)
    basket = BasketView(request)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
        quantity = 1

    if quantity > product.stock:
        logger.info(
            "Basket update limited by stock",
            extra={
                "product_id": product_id,
                "user_id": request.user.id,
                "requested": quantity,
                "stock": product.stock,
            },
        )
        quantity = product.stock

    if quantity > 0:
        basket.add(product, quantity=quantity, update_quantity=True)
        logger.info(
            "Basket quantity updated",
            extra={
                "product_id": product_id,
                "user_id": request.user.id,
                "quantity": quantity,
            },
        )
    else:
        basket.remove(product)
        logger.info(
            "Product removed from basket due to zero quantity",
            extra={
                "product_id": product_id,
                "user_id": request.user.id,
            },
        )

    if request.headers.get("HX-Request") == "true":
        return render(
            request, "catalog/partials/basket_content.html", {"basket": basket}
        )

    return redirect("basket_detail")


@require_POST
@login_required
def basket_clear(request: HttpRequest) -> HttpResponse:
    basket = BasketView(request)
    basket.clear()
    logger.info("Basket cleared", extra={"user_id": request.user.id})

    if request.headers.get("HX-Request") == "true":
        return render(
            request, "catalog/partials/basket_content.html", {"basket": basket}
        )

    return redirect("basket_detail")
