from django.urls import path

from .basket_views import (
    basket_add,
    basket_clear,
    basket_detail,
    basket_remove,
    basket_update,
)
from .info_views import (
    contact_info,
    refund_policy,
    terms_and_conditions,
)
from .order_views import (
    order_cancel,
    order_create,
    order_detail,
    order_list,
    order_payment,
    order_payment_callback,
    order_payment_process,
)
from .views import (
    ProductCreateView,
    ProductDeleteView,
    ProductDetailView,
    ProductListView,
    ProductUpdateView,
    delete_main_product_image,
    delete_product_image,
    pagination_cards_view,
    product_delete_view,
    product_filter_view,
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
    path(
        "product/<int:product_id>/image/<int:image_id>/delete/",
        delete_product_image,
        name="delete_product_image",
    ),
    path(
        "product/<int:product_id>/main-image/delete/",
        delete_main_product_image,
        name="delete_main_product_image",
    ),
    path("basket/", basket_detail, name="basket_detail"),
    path("basket/add/<int:product_id>/", basket_add, name="basket_add"),
    path("basket/remove/<int:product_id>/", basket_remove, name="basket_remove"),
    path("basket/update/<int:product_id>/", basket_update, name="basket_update"),
    path("basket/clear/", basket_clear, name="basket_clear"),
    path("order/create/", order_create, name="order_create"),
    path("order/<int:pk>/", order_detail, name="order_detail"),
    path("order/<int:pk>/cancel/", order_cancel, name="order_cancel"),
    path("order/<int:pk>/payment/", order_payment, name="order_payment"),
    path(
        "order/<int:pk>/payment/process/",
        order_payment_process,
        name="order_payment_process",
    ),
    path("payment/callback/", order_payment_callback, name="order_payment_callback"),
    path("orders/", order_list, name="order_list"),
    path("terms/", terms_and_conditions, name="terms_and_conditions"),
    path("refund/", refund_policy, name="refund_policy"),
    path("contact/", contact_info, name="contact_info"),
]
