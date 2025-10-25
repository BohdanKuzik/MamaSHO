from django.urls import path

from .views import (
    ProductListView,
    ProductDetailView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
    product_search_view,
    product_delete_view,
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
    path("product/search/", product_search_view, name="product_search"),
]
