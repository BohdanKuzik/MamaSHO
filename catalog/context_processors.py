from .basket import BasketView


def basket(request):
    if request.user.is_authenticated:
        return {"basket": BasketView(request)}
    return {"basket": None}
