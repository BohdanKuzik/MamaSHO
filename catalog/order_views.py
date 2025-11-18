from __future__ import annotations

import json
import logging
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods

from .basket import BasketView, SessionBasket
from .forms import OrderForm
from .models import Customer, Order, OrderItem, Product
from .payment_wayforpay import WayForPay


logger = logging.getLogger(__name__)


def send_order_notification_email(order: Order) -> None:
    """Send email notification to admin about new order"""
    try:
        notification_email = getattr(settings, "ORDER_NOTIFICATION_EMAIL", "kuzikbv2509@gmail.com")
        
        if not notification_email:
            logger.warning("ORDER_NOTIFICATION_EMAIL not configured, skipping email notification")
            return
        
        # Support multiple recipients: comma-separated string or list
        if isinstance(notification_email, str):
            # Split by comma and strip whitespace
            recipients = [email.strip() for email in notification_email.split(",") if email.strip()]
        else:
            # Already a list
            recipients = list(notification_email)
        
        if not recipients:
            logger.warning("No valid email recipients configured, skipping email notification")
            return
        
        # Check email configuration
        email_host_user = getattr(settings, "EMAIL_HOST_USER", "")
        email_host_password = getattr(settings, "EMAIL_HOST_PASSWORD", "")
        email_backend = getattr(settings, "EMAIL_BACKEND", "")
        
        if not email_host_user:
            logger.error(
                "EMAIL_HOST_USER not configured. Cannot send email.",
                extra={"order_id": order.id}
            )
            return
        
        if not email_host_password:
            logger.error(
                "EMAIL_HOST_PASSWORD not configured. Cannot send email.",
                extra={"order_id": order.id}
            )
            return
        
        logger.info(
            "Attempting to send order notification email",
            extra={
                "order_id": order.id,
                "recipients": recipients,
                "from_email": email_host_user,
                "email_backend": email_backend,
                "email_host": getattr(settings, "EMAIL_HOST", ""),
            }
        )
        
        subject = f"Нове замовлення #{order.id} - MamaSHO"
        
        html_message = render_to_string(
            "catalog/emails/order_notification.html",
            {"order": order}
        )
        
        from_email = email_host_user
        
        send_mail(
            subject=subject,
            message="",
            from_email=from_email,
            recipient_list=recipients,
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(
            "Order notification email sent successfully",
            extra={"order_id": order.id, "recipients": recipients}
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(
            "Failed to send order notification email",
            extra={
                "order_id": order.id,
                "error": error_msg,
                "error_type": type(e).__name__,
                "email_host_user": getattr(settings, "EMAIL_HOST_USER", "NOT_SET"),
                "email_host": getattr(settings, "EMAIL_HOST", "NOT_SET"),
                "email_backend": getattr(settings, "EMAIL_BACKEND", "NOT_SET"),
            },
            exc_info=True,
        )


def send_customer_order_created_email(order: Order, request: HttpRequest) -> None:
    """Send email to customer when order is created"""
    try:
        if not order.email:
            logger.warning(f"Order {order.id} has no email, skipping customer notification")
            return
        
        email_host_user = getattr(settings, "EMAIL_HOST_USER", "")
        if not email_host_user:
            logger.error("EMAIL_HOST_USER not configured. Cannot send email.")
            return
        
        payment_url = request.build_absolute_uri(reverse("order_payment", kwargs={"pk": order.id}))
        order_detail_url = request.build_absolute_uri(reverse("order_detail", kwargs={"pk": order.id}))
        
        subject = f"Ваше замовлення #{order.id} прийнято - MamaSHO"
        
        html_message = render_to_string(
            "catalog/emails/order_created.html",
            {
                "order": order,
                "payment_url": payment_url,
                "order_detail_url": order_detail_url,
            }
        )
        
        send_mail(
            subject=subject,
            message="",  # HTML only, no plain text
            from_email=email_host_user,
            recipient_list=[order.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(
            "Customer order created email sent successfully",
            extra={"order_id": order.id, "email": order.email}
        )
    except Exception as e:
        logger.error(
            "Failed to send customer order created email",
            extra={"order_id": order.id, "error": str(e)},
            exc_info=True,
        )


def send_customer_order_paid_email(order: Order, request: HttpRequest) -> None:
    """Send email to customer when order is paid"""
    try:
        if not order.email:
            logger.warning(f"Order {order.id} has no email, skipping paid notification")
            return
        
        email_host_user = getattr(settings, "EMAIL_HOST_USER", "")
        if not email_host_user:
            logger.error("EMAIL_HOST_USER not configured. Cannot send email.")
            return
        
        order_detail_url = request.build_absolute_uri(reverse("order_detail", kwargs={"pk": order.id}))
        
        subject = f"Оплата замовлення #{order.id} підтверджена - MamaSHO"
        
        html_message = render_to_string(
            "catalog/emails/order_paid.html",
            {
                "order": order,
                "order_detail_url": order_detail_url,
            }
        )
        
        send_mail(
            subject=subject,
            message="",  # HTML only, no plain text
            from_email=email_host_user,
            recipient_list=[order.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(
            "Customer order paid email sent successfully",
            extra={"order_id": order.id, "email": order.email}
        )
    except Exception as e:
        logger.error(
            "Failed to send customer order paid email",
            extra={"order_id": order.id, "error": str(e)},
            exc_info=True,
        )


def send_customer_order_status_changed_email(order: Order, old_status: str | None = None, request: HttpRequest | None = None) -> None:
    """Send email to customer when order status changes"""
    try:
        if not order.email:
            logger.warning(f"Order {order.id} has no email, skipping status change notification")
            return
        
        email_host_user = getattr(settings, "EMAIL_HOST_USER", "")
        if not email_host_user:
            logger.error("EMAIL_HOST_USER not configured. Cannot send email.")
            return
        
        # Build order detail URL
        if request:
            order_detail_url = request.build_absolute_uri(reverse("order_detail", kwargs={"pk": order.id}))
        else:
            # Fallback if no request available (e.g., from admin)
            site_url = getattr(settings, "SITE_URL", "https://mamasho.onrender.com")
            order_detail_url = f"{site_url}/order/{order.id}/"
        
        subject = f"Статус замовлення #{order.id} змінено - MamaSHO"
        
        html_message = render_to_string(
            "catalog/emails/order_status_changed.html",
            {
                "order": order,
                "old_status": old_status,
                "order_detail_url": order_detail_url,
            }
        )
        
        send_mail(
            subject=subject,
            message="",  # HTML only, no plain text
            from_email=email_host_user,
            recipient_list=[order.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(
            "Customer order status changed email sent successfully",
            extra={"order_id": order.id, "email": order.email, "new_status": order.status, "old_status": old_status}
        )
    except Exception as e:
        logger.error(
            "Failed to send customer order status changed email",
            extra={"order_id": order.id, "error": str(e)},
            exc_info=True,
        )


def get_basket_for_order(request: HttpRequest) -> BasketView | SessionBasket | None:
    if request.user.is_authenticated:
        try:
            return BasketView(request)
        except ValueError:
            return None
    return SessionBasket(request)


@login_required
def order_create(request: HttpRequest) -> HttpResponse:
    basket = get_basket_for_order(request)

    if not basket or len(basket) == 0:
        messages.error(request, "Ваш кошик порожній. Додайте товари перед оформленням замовлення.")
        return redirect("basket_detail")

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    customer, _ = Customer.objects.get_or_create(user=request.user)

                    order = form.save(commit=False)
                    order.customer = customer
                    order.total_price = basket.get_total_price()
                    order.save()

                    for item in basket:
                        product = item["product"]
                        quantity = item["quantity"]

                        if quantity > product.stock:
                            messages.error(
                                request,
                                f"Недостатньо товару '{product.name}' на складі. "
                                f"Доступно: {product.stock}, запитано: {quantity}",
                            )
                            order.delete()
                            return render(
                                request,
                                "catalog/order_create.html",
                                {"form": form, "basket": basket},
                            )

                        OrderItem.objects.create(
                            order=order, product=product, quantity=quantity
                        )

                        product.stock -= quantity
                        product.save()

                    basket.clear()

                    logger.info(
                        "Order created",
                        extra={
                            "order_id": order.id,
                            "user_id": request.user.id,
                            "total_price": float(order.total_price),
                        },
                    )

                    # Send email notification to admin
                    try:
                        send_order_notification_email(order)
                    except Exception as e:
                        logger.error(
                            "Failed to send order notification email",
                            extra={"order_id": order.id, "error": str(e)},
                            exc_info=True,
                        )
                        # Don't fail the order creation if email fails
                        messages.warning(
                            request,
                            "Замовлення створено, але не вдалося надіслати повідомлення адміністратору.",
                        )
                    
                    # Send email to customer with order details and payment link
                    try:
                        send_customer_order_created_email(order, request)
                    except Exception as e:
                        logger.error(
                            "Failed to send customer order created email",
                            extra={"order_id": order.id, "error": str(e)},
                            exc_info=True,
                        )
                        # Don't fail the order creation if email fails
                        messages.warning(
                            request,
                            "Замовлення створено, але не вдалося надіслати повідомлення на email.",
                        )

                    messages.success(
                        request,
                        f"Замовлення #{order.id} успішно створено!",
                    )
                    
                    if order.payment_method == "card_online":
                        return redirect("order_payment", pk=order.id)
                    
                    return redirect("order_detail", pk=order.id)

            except Exception as e:
                logger.error(
                    "Error creating order",
                    extra={"user_id": request.user.id, "error": str(e)},
                    exc_info=True,
                )
                messages.error(
                    request,
                    "Сталася помилка при створенні замовлення. Будь ласка, спробуйте ще раз.",
                )
    else:
        customer, _ = Customer.objects.get_or_create(user=request.user)
        initial_data = {}
        if customer.phone:
            initial_data["delivery_phone"] = customer.phone
        if customer.address:
            initial_data["delivery_address"] = customer.address
        if request.user.email:
            initial_data["email"] = request.user.email

        form = OrderForm(initial=initial_data)

    return render(
        request, "catalog/order_create.html", {"form": form, "basket": basket}
    )


@login_required
def order_detail(request: HttpRequest, pk: int) -> HttpResponse:
    order = get_object_or_404(Order, pk=pk, customer__user=request.user)
    return render(request, "catalog/order_detail.html", {"order": order})


@login_required
def order_list(request: HttpRequest) -> HttpResponse:
    customer, _ = Customer.objects.get_or_create(user=request.user)
    orders = Order.objects.filter(customer=customer).select_related("customer").prefetch_related("items__product")
    return render(request, "catalog/order_list.html", {"orders": orders})


@login_required
@require_POST
def order_cancel(request: HttpRequest, pk: int) -> HttpResponse:
    order = get_object_or_404(Order, pk=pk, customer__user=request.user)

    if not order.can_be_cancelled():
        messages.error(
            request,
            "Неможливо скасувати замовлення в поточному статусі. "
            "Зверніться до служби підтримки.",
        )
        return redirect("order_detail", pk=pk)

    try:
        order.cancel()
        logger.info(
            "Order cancelled by user",
            extra={"order_id": order.id, "user_id": request.user.id},
        )
        messages.success(
            request,
            f"Замовлення #{order.id} скасовано. Товари повернуто на склад.",
        )
    except Exception as e:
        logger.error(
            "Error cancelling order",
            extra={"order_id": order.id, "user_id": request.user.id, "error": str(e)},
            exc_info=True,
        )
        messages.error(request, "Сталася помилка при скасуванні замовлення.")

    return redirect("order_detail", pk=pk)


@login_required
def order_payment(request: HttpRequest, pk: int) -> HttpResponse:
    order = get_object_or_404(Order, pk=pk, customer__user=request.user)

    if order.payment_status == "paid":
        messages.info(request, "Це замовлення вже оплачено.")
        return redirect("order_detail", pk=pk)

    if order.payment_method != "card_online":
        messages.warning(request, "Для цього замовлення не потрібна онлайн оплата.")
        return redirect("order_detail", pk=pk)

    merchant_account = getattr(settings, "WAYFORPAY_MERCHANT_ACCOUNT", "")
    merchant_secret = getattr(settings, "WAYFORPAY_MERCHANT_SECRET_KEY", "")

    if not merchant_account or not merchant_secret:
        logger.warning(
            "WayForPay credentials not configured",
            extra={"order_id": order.id}
        )
        messages.warning(
            request,
            "Платіжна система не налаштована. Використовується тестовий режим.",
        )
        return render(request, "catalog/order_payment.html", {"order": order, "test_mode": True})

    sandbox = getattr(settings, "WAYFORPAY_SANDBOX", False)
    wayforpay = WayForPay(merchant_account, merchant_secret, sandbox=sandbox)
    
    logger.info(
        "Creating WayForPay payment",
        extra={
            "order_id": order.id,
            "amount": float(order.total_price),
            "sandbox_mode": sandbox,
            "merchant_account": merchant_account,
        }
    )

    return_url = request.build_absolute_uri(
        reverse("order_payment_process", kwargs={"pk": order.pk})
    )
    service_url = request.build_absolute_uri(reverse("order_payment_callback"))

    customer = order.customer
    client_name = f"{customer.user.first_name} {customer.user.last_name}".strip() or customer.user.username
    client_email = customer.user.email or ""
    client_phone = order.delivery_phone or customer.phone or ""

    unique_suffix = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = uuid4().hex[:6]
    wayforpay_reference = f"{order.id}-{unique_suffix}-{random_part}"

    payment_data = wayforpay.create_payment_form(
        order_id=wayforpay_reference,
        amount=order.total_price,
        currency="UAH",
        product_name=f"Замовлення #{order.id}",
        client_name=client_name,
        client_email=client_email,
        client_phone=client_phone,
        return_url=return_url,
        service_url=service_url,
    )

    payment_form_html = wayforpay.get_payment_form_html(payment_data)

    return render(
        request,
        "catalog/order_payment.html",
        {
            "order": order,
            "payment_form_html": payment_form_html,
            "payment_data": payment_data,
            "wayforpay_url": wayforpay.base_url,
            "test_mode": sandbox,
        },
    )


@csrf_exempt
@login_required
@require_http_methods(["GET", "POST"])
def order_payment_process(request: HttpRequest, pk: int) -> HttpResponse:
    order = get_object_or_404(Order, pk=pk, customer__user=request.user)

    if order.payment_status == "paid":
        messages.success(request, "Оплата замовлення успішно виконана!")
        return redirect("order_detail", pk=pk)
    elif order.payment_status == "failed":
        messages.error(request, "Помилка при оплаті замовлення. Спробуйте ще раз.")
        return redirect("order_payment", pk=pk)

    messages.info(request, "Оплата обробляється. Оновіть сторінку через кілька секунд.")
    return redirect("order_detail", pk=pk)


@csrf_exempt
@require_http_methods(["POST"])
def order_payment_callback(request: HttpRequest) -> HttpResponse:
    merchant_account = getattr(settings, "WAYFORPAY_MERCHANT_ACCOUNT", "")
    merchant_secret = getattr(settings, "WAYFORPAY_MERCHANT_SECRET_KEY", "")

    if not merchant_account or not merchant_secret:
        logger.error("WayForPay keys not configured")
        return JsonResponse({"status": "error", "message": "Configuration error"}, status=500)

    wayforpay = WayForPay(merchant_account, merchant_secret)

    # Отримуємо дані від WayForPay
    try:
        if request.content_type and "application/json" in request.content_type:
            callback_data = json.loads(request.body.decode("utf-8"))
        elif request.method == "POST" and request.POST:
            callback_data = {}
            for key, value in request.POST.items():
                callback_data[key] = value
        else:
            try:
                callback_data = json.loads(request.body.decode("utf-8"))
            except:
                callback_data = {}
    except Exception as e:
        logger.error(f"WayForPay callback: error parsing data - {e}")
        return JsonResponse({"status": "error", "message": "Invalid data"}, status=400)

    if not wayforpay.verify_callback_signature(callback_data):
        logger.warning("WayForPay callback: invalid signature")
        return JsonResponse({"status": "error", "message": "Invalid signature"}, status=400)

    order_reference = str(callback_data.get("orderReference", ""))
    order_id_part = order_reference.split("-")[0] if order_reference else ""
    transaction_status = callback_data.get("transactionStatus")
    amount = callback_data.get("amount")
    reason_code = callback_data.get("reasonCode")
    reason = callback_data.get("reason", "")

    if not order_id_part:
        logger.warning("WayForPay callback: missing orderReference")
        return JsonResponse({"status": "error", "message": "Missing order reference"}, status=400)

    try:
        order = Order.objects.get(pk=int(order_id_part))
    except (Order.DoesNotExist, ValueError):
        logger.warning(f"WayForPay callback: order not found - {order_reference}")
        return JsonResponse({"status": "error", "message": "Order not found"}, status=404)

    try:
        with transaction.atomic():
            if transaction_status == "Approved":
                try:
                    callback_amount = Decimal(str(amount))
                    if callback_amount != order.total_price:
                        logger.warning(
                            f"WayForPay callback: amount mismatch - expected {order.total_price}, got {callback_amount}",
                            extra={"order_id": order.id},
                        )
                        return JsonResponse(
                            {"status": "error", "message": "Amount mismatch"}, status=400
                        )
                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"WayForPay callback: invalid amount format - {amount}",
                        extra={"order_id": order.id, "error": str(e)},
                    )

                if order.payment_status != "paid":
                    order.payment_status = "paid"
                    order.paid_at = datetime.now()
                    order.save()

                    logger.info(
                        "Order payment confirmed via WayForPay",
                        extra={
                            "order_id": order.id,
                            "amount": amount,
                            "reason_code": reason_code,
                        },
                    )
                    
                    # Send email to customer about payment confirmation
                    try:
                        # Build request object for URL generation
                        from django.test import RequestFactory
                        factory = RequestFactory()
                        fake_request = factory.get('/')
                        fake_request.META['HTTP_HOST'] = request.META.get('HTTP_HOST', 'mamasho.onrender.com')
                        fake_request.scheme = request.scheme if hasattr(request, 'scheme') else 'https'
                        send_customer_order_paid_email(order, fake_request)
                    except Exception as e:
                        logger.error(
                            "Failed to send customer order paid email",
                            extra={"order_id": order.id, "error": str(e)},
                            exc_info=True,
                        )

                return JsonResponse(
                    {
                        "orderReference": order_reference,
                        "status": "accept",
                        "time": int(datetime.now().timestamp()),
                    }
                )

            elif transaction_status in ("Declined", "Refunded", "Expired"):
                order.payment_status = "failed"
                order.save()

                logger.warning(
                    f"WayForPay payment failed for order {order.id}",
                    extra={
                        "order_id": order.id,
                        "status": transaction_status,
                        "reason": reason,
                        "reason_code": reason_code,
                    },
                )

                return JsonResponse(
                    {
                        "orderReference": order_reference,
                        "status": "accept",
                        "time": int(datetime.now().timestamp()),
                    }
                )
            else:
                logger.info(
                    f"WayForPay callback: status {transaction_status} for order {order.id}",
                    extra={"order_id": order.id, "status": transaction_status},
                )

                return JsonResponse(
                    {
                        "orderReference": order_reference,
                        "status": "accept",
                        "time": int(datetime.now().timestamp()),
                    }
                )

    except Exception as e:
        logger.error(
            f"WayForPay callback: error processing payment - {e}",
            extra={"order_id": order_id_part, "order_reference": order_reference},
            exc_info=True,
        )
        return JsonResponse({"status": "error", "message": "Processing error"}, status=500)
