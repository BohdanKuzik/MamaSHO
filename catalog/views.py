from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test

from catalog.models import Product, Category
from catalog.forms import CreateProductForm, UpdateProductForm


def apply_product_filters(products, request):
    """Apply filters to products based on request parameters"""
    category_id = request.GET.get("category", "")
    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")
    available_only = request.GET.get("available", "")
    search_query = request.GET.get("search", "")

    products = products.distinct()

    if category_id:
        products = products.filter(category_id=category_id)

    if max_price and max_price != "" and max_price != "0":
        products = products.filter(price__lte=max_price)

    if min_price and min_price != "" and min_price != "0":
        products = products.filter(price__gte=min_price)

    if available_only in ["True", True, "on"]:
        products = products.filter(available=True)

    if search_query:
        search_lower = search_query.lower().strip()
        if search_lower:
            seen_ids = set()
            filtered_product_ids = []

            for product in products:
                if product.id in seen_ids:
                    continue

                product_name_lower = product.name.lower() if product.name else ""
                category_name_lower = (
                    product.category.name.lower()
                    if product.category and product.category.name
                    else ""
                )

                if (
                    search_lower in product_name_lower
                    or search_lower in category_name_lower
                ):
                    filtered_product_ids.append(product.id)
                    seen_ids.add(product.id)

            if filtered_product_ids:
                products = products.filter(id__in=filtered_product_ids).distinct()
            else:
                products = products.none()

    return products.distinct()


class ProductListView(ListView):
    model = Product
    template_name = "catalog/product_list.html"
    context_object_name = "products"
    paginate_by = 15

    def get_queryset(self):
        products = Product.objects.all()
        return apply_product_filters(products, self.request)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context["amount"] = self.model.objects.count()
        context["categories"] = Category.objects.all()
        return context


def product_filter_view(request):
    is_htmx = request.headers.get("HX-Request") == "true"
    if not is_htmx:
        return None

    products = Product.objects.all()
    products = apply_product_filters(products, request)
    amount_after_filter = products.count()

    return render(
        request,
        "catalog/partials/search_results.html",
        context={"products": products, "amount_after_filter": amount_after_filter},
    )


class ProductDetailView(DetailView):
    model = Product
    template_name = "catalog/product_detail.html"
    context_object_name = "product"


class ProductCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Product
    form_class = CreateProductForm
    template_name = "catalog/add_product.html"
    context_object_name = "add_product"
    success_url = reverse_lazy("product_list")

    def test_func(self):
        user = self.request.user
        return user.is_staff or user.is_superuser


class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Product
    form_class = UpdateProductForm
    template_name = "catalog/product_update.html"
    success_url = reverse_lazy("product_list")

    def test_func(self):
        user = self.request.user
        return user.is_staff or user.is_superuser


class ProductDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Product
    template_name = "catalog/product_confirm_delete.html"
    success_url = reverse_lazy("product_list")

    def test_func(self):
        user = self.request.user
        return user.is_staff or user.is_superuser


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def product_delete_view(request, pk):
    obj = get_object_or_404(Product, pk=pk)

    if not request.method == "DELETE":
        return None
    obj.delete()
    amount = Product.objects.count()
    return render(
        request, "catalog/partials/product_count.html", context={"amount": amount}
    )


def pagination_cards_view(request):
    page_number = request.GET.get("page")
    product_list = Product.objects.all()

    product_list = apply_product_filters(product_list, request)

    paginator = Paginator(product_list, 15)
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        "catalog/partials/pagination_cards.html",
        context={"products": page_obj.object_list, "page_obj": page_obj},
    )
