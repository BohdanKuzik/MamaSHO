from __future__ import annotations

from typing import Dict, Optional

from django.http import HttpRequest

from .basket import BasketView


def basket(request: HttpRequest) -> Dict[str, Optional[BasketView]]:
    if request.user.is_authenticated:
        return {"basket": BasketView(request)}
    return {"basket": None}
