from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Product


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return [
            "product_list",
            "terms_and_conditions",
            "refund_policy",
            "contact_info",
        ]

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    priority = 0.9
    changefreq = "daily"

    def items(self):
        return Product.objects.filter(available=True)

    def lastmod(self, obj: Product):
        return obj.created_at

    def location(self, obj: Product):
        return reverse("product_detail", kwargs={"pk": obj.pk})


sitemaps = {
    "static": StaticViewSitemap,
    "products": ProductSitemap,
}
