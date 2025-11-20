from __future__ import annotations

from django.contrib.sitemaps import Sitemap
from django.db.models import QuerySet
from django.urls import reverse
from django.utils import timezone

from .models import Product


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self: "StaticViewSitemap") -> list[str]:
        return [
            "product_list",
            "terms_and_conditions",
            "refund_policy",
            "contact_info",
        ]

    def location(self: "StaticViewSitemap", item: str) -> str:
        return reverse(item)


class ProductSitemap(Sitemap):
    priority = 0.9
    changefreq = "daily"

    def items(self: "ProductSitemap") -> QuerySet[Product]:
        return Product.objects.filter(available=True)

    def lastmod(self: "ProductSitemap", obj: Product) -> timezone.datetime:
        return obj.created_at

    def location(self: "ProductSitemap", obj: Product) -> str:
        return reverse("product_detail", kwargs={"pk": obj.pk})


sitemaps = {
    "static": StaticViewSitemap,
    "products": ProductSitemap,
}
