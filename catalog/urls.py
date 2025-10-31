from django.urls import path

from .views import (
    ProductListView,
    ProductDetailView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
    product_delete_view,
    pagination_cards_view,
    product_filter_view,
)
from .basket_views import (
    basket_detail,
    basket_add,
    basket_remove,
    basket_update,
    basket_clear,
)


urlpatterns = [
    path("", ProductListView.as_view(), name="product_list"),
    path("product/<int:pk>/", ProductDetailView.as_view(), name="product_detail"),
    path("product/create/", ProductCreateView.as_view(), name="add_product"),
    path("product/<int:pk>/edit/", ProductUpdateView.as_view(), name="edit_product"),
    path(
        "product/<int:pk>/delete/", ProductDeleteView.as_view(), name="delete_product"
    ),
    path(
        "product/<int:pk>/dynamic-delete/", product_delete_view, name="dynamic-delete"
    ),
    path("product/filter/", product_filter_view, name="product_filter"),
    path("load_more/cards/", pagination_cards_view, name="load_more"),
    path("basket/", basket_detail, name="basket_detail"),
    path("basket/add/<int:product_id>/", basket_add, name="basket_add"),
    path("basket/remove/<int:product_id>/", basket_remove, name="basket_remove"),
    path("basket/update/<int:product_id>/", basket_update, name="basket_update"),
    path("basket/clear/", basket_clear, name="basket_clear"),
]
