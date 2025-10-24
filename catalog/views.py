from http.client import HTTPResponse

from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)

from catalog.models import Product
from catalog.forms import CreateProductForm, UpdateProductForm


class ProductListView(ListView):
    model = Product
    template_name = "catalog/product_list.html"
    context_object_name = "products"


class ProductDetailView(DetailView):
    model = Product
    template_name = "catalog/product_detail.html"
    context_object_name = "product"


class ProductCreateView(CreateView):
    model = Product
    form_class = CreateProductForm
    template_name = "catalog/add_product.html"
    context_object_name = "add_product"
    success_url = reverse_lazy("product_list")


class ProductUpdateView(UpdateView):
    model = Product
    form_class = UpdateProductForm
    template_name = "catalog/product_update.html"
    success_url = reverse_lazy("product_list")


class ProductDeleteView(DeleteView):
    model = Product
    template_name = "catalog/product_confirm_delete.html"
    success_url = reverse_lazy("product_list")


def product_search_view(request):
    is_htmx = request.headers.get("HX_Request") == "true"
    search_query = request.GET.get("search", "")

    if not is_htmx:
        return None

    if search_query:
        filtered_products = Product.objects.filter(name__icontains=search_query)
    else:
        filtered_products = Product.objects.all()
    return render(
        request,
        "catalog/partials/search_results.html",
        context={"products": filtered_products},
    )
