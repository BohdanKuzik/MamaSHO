from __future__ import annotations

from typing import Dict

from django.conf import settings
from django.http import HttpRequest

from .basket import BasketView, SessionBasket


def basket(request: HttpRequest) -> Dict[str, BasketView | SessionBasket]:
    """Context processor для кошика"""
    if request.user.is_authenticated:
        try:
            basket_obj = BasketView(request)
        except ValueError:
            basket_obj = SessionBasket(request)
    else:
        basket_obj = SessionBasket(request)

    return {"basket": basket_obj}


def seo(request: HttpRequest) -> Dict[str, str]:
    """Context processor для SEO мета-даних"""
    site_url = getattr(settings, "SITE_URL", "https://mamasho.store").rstrip("/")

    return {
        "site_url": site_url,
        "site_name": "MamaSHO",
        "default_description": (
            "MamaSHO - інтернет-магазин дитячих товарів. "
            "Широкий вибір якісних товарів для дітей різного віку. "
            "Швидка доставка по всій Україні."
        ),
        "default_keywords": (
            "дитячі товари, інтернет-магазин, дитячий одяг, "
            "іграшки для дітей, товари для дітей Україна"
        ),
    }
