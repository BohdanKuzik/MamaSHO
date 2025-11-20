from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def terms_and_conditions(request: HttpRequest) -> HttpResponse:
    """Terms and Conditions page"""
    return render(request, "catalog/info/terms_and_conditions.html")


def refund_policy(request: HttpRequest) -> HttpResponse:
    """Refund Policy page"""
    return render(request, "catalog/info/refund_policy.html")


def contact_info(request: HttpRequest) -> HttpResponse:
    """Contact Information page"""
    return render(request, "catalog/info/contact_info.html")
