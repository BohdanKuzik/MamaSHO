from __future__ import annotations

from typing import Dict, Optional

from django.http import HttpRequest

from .basket import BasketView, SessionBasket


def basket(request: HttpRequest) -> Dict[str, Optional[BasketView | SessionBasket]]:
    if request.user.is_authenticated:
        try:
            return {"basket": BasketView(request)}
        except ValueError:
            return {"basket": None}
    return {"basket": SessionBasket(request)}
