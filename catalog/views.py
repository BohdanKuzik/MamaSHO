from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView

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
    template_name = "catalog/add_product.html"
    context_object_name = "add_product"
    form_class = CreateProductForm
    success_url = reverse_lazy("product_list")


class ProductUpdateView(UpdateView):
    model = Product
    template_name = "catalog/product_update.html"
    form_class = UpdateProductForm
    success_url = reverse_lazy("product_list")
