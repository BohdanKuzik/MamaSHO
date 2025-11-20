from __future__ import annotations

import json
from typing import Dict, Iterable, Optional

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db import models
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from catalog.forms import CreateProductForm, UpdateProductForm
from catalog.models import Category, Product, ProductImage


def apply_product_filters(
    products: QuerySet[Product], request: HttpRequest
) -> QuerySet[Product]:
    products = products.distinct()

    filter_config = {
        "category": ("category_id", "equals"),
        "min_price": ("price__gte", "numeric"),
        "max_price": ("price__lte", "numeric"),
    }

    for param_key, (filter_key, filter_type) in filter_config.items():
        value = request.GET.get(param_key, "").strip()

        if filter_type == "numeric":
            if value and value != "0":
                try:
                    numeric_value = float(value)
                    products = products.filter(**{filter_key: numeric_value})
                except (ValueError, TypeError):
                    pass
        elif filter_type == "equals":
            if value:
                products = products.filter(**{filter_key: value})

    available_only = request.GET.get("available", "")
    if available_only in ["True", True, "on", 1, "true"]:
        products = products.filter(available=True)

    search_query = request.GET.get("search", "").strip()
    if search_query:
        search_lower = search_query.lower()
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

    def get_queryset(self: "ProductListView") -> QuerySet[Product]:
        products = Product.objects.all()
        return apply_product_filters(products, self.request)

    def get_context_data(
        self: "ProductListView",
        *,
        object_list: Optional[Iterable[Product]] = None,
        **kwargs: object,
    ) -> Dict[str, object]:
        context = super().get_context_data(object_list=object_list, **kwargs)
        context["amount"] = self.model.objects.count()
        context["categories"] = Category.objects.all()
        return context


def product_filter_view(request: HttpRequest) -> Optional[HttpResponse]:
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

    def test_func(self: "ProductCreateView") -> bool:
        user = self.request.user
        return user.is_staff or user.is_superuser

    def get_success_url(self: "ProductCreateView") -> str:
        return reverse("product_detail", kwargs={"pk": self.object.pk})

    def form_valid(self: "ProductCreateView", form: CreateProductForm) -> HttpResponse:
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
        if self.request.headers.get("HX-Request") == "true":
            form_instance = self.get_form_class()()
            context = self.get_context_data(form=form_instance)
            context["product"] = self.object
            hx_response = render(
                self.request,
                "catalog/partials/add_product_form.html",
                context,
                status=200,
            )
            hx_response["HX-Trigger-After-Settle"] = json.dumps(
                {
                    "show-toast": {
                        "message": f'Товар "{self.object.name}" успішно створено!',
                        "type": "success",
                    }
                }
            )
            return hx_response
        return response

    def form_invalid(
        self: "ProductCreateView", form: CreateProductForm
    ) -> HttpResponse:
        if self.request.headers.get("HX-Request") == "true":
            context = self.get_context_data(form=form)
            return render(
                self.request,
                "catalog/partials/add_product_form.html",
                context,
                status=200,
            )
        return super().form_invalid(form)


class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Product
    form_class = UpdateProductForm
    template_name = "catalog/product_update.html"

    def test_func(self: "ProductUpdateView") -> bool:
        user = self.request.user
        return user.is_staff or user.is_superuser

    def get_success_url(self: "ProductUpdateView") -> str:
        return reverse("product_detail", kwargs={"pk": self.object.pk})

    def form_valid(self: "ProductUpdateView", form: UpdateProductForm) -> HttpResponse:
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
        if self.request.headers.get("HX-Request") == "true":
            refreshed_form = self.get_form_class()(instance=self.object)
            context = self.get_context_data(form=refreshed_form)
            hx_response = render(
                self.request,
                "catalog/partials/product_update_form.html",
                context,
                status=200,
            )
            hx_response["HX-Trigger-After-Settle"] = json.dumps(
                {
                    "show-toast": {
                        "message": f'Зміни товару "{self.object.name}" збережено!',
                        "type": "success",
                    }
                }
            )
            return hx_response
        return response

    def form_invalid(
        self: "ProductUpdateView", form: UpdateProductForm
    ) -> HttpResponse:
        if self.request.headers.get("HX-Request") == "true":
            context = self.get_context_data(form=form)
            return render(
                self.request,
                "catalog/partials/product_update_form.html",
                context,
                status=200,
            )
        return super().form_invalid(form)


class ProductDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Product
    template_name = "catalog/product_confirm_delete.html"
    success_url = reverse_lazy("product_list")

    def test_func(self: "ProductDeleteView") -> bool:
        user = self.request.user
        return user.is_staff or user.is_superuser


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def product_delete_view(request: HttpRequest, pk: int) -> Optional[HttpResponse]:
    obj = get_object_or_404(Product, pk=pk)

    if not request.method == "DELETE":
        return None
    obj.delete()
    amount = Product.objects.count()

    if request.headers.get("HX-Request") == "true":
        from django.http import HttpResponse

        response = HttpResponse("")
        response["HX-Trigger"] = json.dumps({"product-deleted": {"amount": amount}})
        return response

    return render(
        request, "catalog/partials/product_count.html", context={"amount": amount}
    )


def pagination_cards_view(request: HttpRequest) -> HttpResponse:
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
def delete_product_image(
    request: HttpRequest, product_id: int, image_id: int
) -> HttpResponse:
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
def delete_main_product_image(request: HttpRequest, product_id: int) -> HttpResponse:
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
