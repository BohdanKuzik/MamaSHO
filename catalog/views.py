from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import models
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from catalog.models import Product, Category, ProductImage
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

    if available_only in ["True", True, "on", 1, "true"]:
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

    def test_func(self):
        user = self.request.user
        return user.is_staff or user.is_superuser

    def get_success_url(self):
        return reverse("product_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        images = []
        index = 0
        while True:
            image_key = f"images_{index}"
            image_file = self.request.FILES.get(image_key)
            if not image_file:
                break
            images.append(image_file)
            index += 1

        if images:
            self.object.image = images[0]
            self.object.save()

            ProductImage.objects.filter(product=self.object, order=0).delete()

            for order, image in enumerate(images[1:], start=1):
                ProductImage.objects.create(
                    product=self.object, image=image, order=order
                )
        return response


class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Product
    form_class = UpdateProductForm
    template_name = "catalog/product_update.html"

    def test_func(self):
        user = self.request.user
        return user.is_staff or user.is_superuser

    def get_success_url(self):
        return reverse("product_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        images = []
        index = 0
        while True:
            image_key = f"images_{index}"
            image_file = self.request.FILES.get(image_key)
            if not image_file:
                break
            images.append(image_file)
            index += 1

        if images:
            max_order = (
                self.object.images.aggregate(max_order=models.Max("order"))["max_order"]
                or -1
            )

            if not self.object.image:
                self.object.image = images[0]
                self.object.save()
                for order, image in enumerate(images[1:], start=1):
                    ProductImage.objects.create(
                        product=self.object, image=image, order=order
                    )
            else:
                for order, image in enumerate(images, start=max_order + 1):
                    ProductImage.objects.create(
                        product=self.object, image=image, order=order
                    )
        return response


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


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
@require_POST
def delete_product_image(request, product_id, image_id):
    product = get_object_or_404(Product, id=product_id)
    image = get_object_or_404(ProductImage, id=image_id, product=product)

    image.image.delete(save=False)
    image.delete()

    product.refresh_from_db()

    if request.headers.get("HX-Request") == "true":
        return render(
            request, "catalog/partials/product_images_list.html", {"product": product}
        )

    return redirect("edit_product", pk=product_id)


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
@require_POST
def delete_main_product_image(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if product.image:
        product.image.delete(save=False)
        product.image = None
        product.save()

    product.refresh_from_db()

    if request.headers.get("HX-Request") == "true":
        return render(
            request, "catalog/partials/product_images_list.html", {"product": product}
        )

    return redirect("edit_product", pk=product_id)
