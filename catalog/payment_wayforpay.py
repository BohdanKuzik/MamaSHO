from __future__ import annotations

import hashlib
import hmac
import logging
import time
from decimal import Decimal
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)


class WayForPay:
    SANDBOX_URL = "https://secure.wayforpay.com/pay"
    PRODUCTION_URL = "https://secure.wayforpay.com/pay"
    API_URL = "https://api.wayforpay.com/api"

    def __init__(
        self: "WayForPay",
        merchant_account: str,
        merchant_secret_key: str,
        sandbox: bool = True,
    ) -> None:
        self.merchant_account = merchant_account
        self.merchant_secret_key = merchant_secret_key
        self.sandbox = sandbox
        self.base_url = self.SANDBOX_URL if sandbox else self.PRODUCTION_URL

    def _generate_signature(self: "WayForPay", fields: list[str]) -> str:
        signature_string = ";".join(str(field) for field in fields)
        signature = hmac.new(
            self.merchant_secret_key.encode("utf-8"),
            signature_string.encode("utf-8"),
            hashlib.md5,
        ).hexdigest()
        return signature

    def create_payment_form(
        self: "WayForPay",
        order_id: str,
        amount: Decimal,
        currency: str,
        product_name: str,
        client_name: str,
        client_email: str,
        client_phone: str,
        return_url: str,
        service_url: str,
    ) -> Dict[str, Any]:
        """
        Створює дані для форми оплати WayForPay

        Args:
            order_id: ID замовлення
            amount: Сума оплати
            currency: Валюта (UAH)
            product_name: Назва товару/послуги
            client_name: Ім'я клієнта
            client_email: Email клієнта
            client_phone: Телефон клієнта
            return_url: URL для повернення після оплати
            service_url: URL для callback від WayForPay

        Returns:
            Dict з даними для форми оплати
        """
        amount_float = float(amount)

        from urllib.parse import urlparse

        parsed_url = urlparse(return_url)
        merchant_domain = parsed_url.netloc or parsed_url.hostname or "localhost"

        order_date = int(time.time())

        fields_for_signature = [
            self.merchant_account,
            merchant_domain,
            order_id,
            str(order_date),
            str(amount_float),  # Use float amount, not cents
            currency,
            product_name,
            "1",  # productCount
            str(amount_float),  # productPrice - same as amount
        ]

        merchant_signature = self._generate_signature(fields_for_signature)

        name_parts = client_name.split() if client_name else []
        client_first_name = name_parts[0] if name_parts else ""
        client_last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        payment_data = {
            "merchantAccount": self.merchant_account,
            "merchantDomainName": merchant_domain,
            "orderReference": order_id,
            "orderDate": order_date,
            "amount": amount_float,
            "currency": currency,
            "productName": [product_name],
            "productCount": [1],
            "productPrice": [amount_float],
            "merchantSignature": merchant_signature,
            "clientFirstName": client_first_name,
            "clientLastName": client_last_name,
            "clientEmail": client_email,
            "clientPhone": client_phone,
            "returnUrl": return_url,
            "serviceUrl": service_url,
            "language": "UA",
        }

        return payment_data

    def verify_callback_signature(self: "WayForPay", data: Dict[str, Any]) -> bool:
        """
        Перевіряє підпис від WayForPay callback

        Згідно з документацією WayForPay, для callback підпис формується з:
        merchantAccount;orderReference;amount;currency;authCode;cardPan;transactionStatus;reasonCode

        Args:
            data: Дані від WayForPay

        Returns:
            True якщо підпис валідний
        """
        try:
            merchant_account = str(data.get("merchantAccount", ""))
            order_reference = str(data.get("orderReference", ""))
            amount = str(data.get("amount", ""))
            currency = str(data.get("currency", ""))
            auth_code = str(data.get("authCode", ""))
            card_pan = str(data.get("cardPan", ""))
            transaction_status = str(data.get("transactionStatus", ""))
            reason_code = str(data.get("reasonCode", ""))

            fields_for_signature = [
                merchant_account,
                order_reference,
                amount,
                currency,
                auth_code,
                card_pan,
                transaction_status,
                reason_code,
            ]

            expected_signature = self._generate_signature(fields_for_signature)
            received_signature = str(data.get("merchantSignature", ""))

            return expected_signature.lower() == received_signature.lower()

        except Exception as e:
            logger.error(f"Error verifying WayForPay signature: {e}")
            return False

    def get_payment_form_html(self: "WayForPay", payment_data: Dict[str, Any]) -> str:
        """
        Генерує HTML форму для оплати через WayForPay

        Args:
            payment_data: Дані для оплати

        Returns:
            HTML код форми
        """
        form_fields = ""
        for key, value in payment_data.items():
            if isinstance(value, list):
                for item in value:
                    form_fields += (
                        f'<input type="hidden" name="{key}[]" value="{item}">\n'
                    )
            else:
                form_fields += f'<input type="hidden" name="{key}" value="{value}">\n'

        html = f"""
        <form method="POST" action="{self.base_url}" id="wayforpay_form">
            {form_fields}
        </form>
        <script>
            document.getElementById('wayforpay_form').submit();
        </script>
        """
        return html

    def check_payment_status(
        self: "WayForPay", order_reference: str
    ) -> Dict[str, Any] | None:
        """
        Перевіряє статус оплати через WayForPay API

        Args:
            order_reference: Посилання на замовлення (orderReference)

        Returns:
            Dict з даними про статус транзакції або None якщо помилка
        """
        try:
            fields_for_signature = [
                self.merchant_account,
                order_reference,
            ]

            merchant_signature = self._generate_signature(fields_for_signature)

            request_data = {
                "transactionType": "CHECK_STATUS",
                "merchantAccount": self.merchant_account,
                "orderReference": order_reference,
                "merchantSignature": merchant_signature,
                "apiVersion": 1,
            }

            response = requests.post(
                self.API_URL,
                json=request_data,
                timeout=10,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code != 200:
                logger.error(
                    f"WayForPay API error: {response.status_code}",
                    extra={
                        "order_reference": order_reference,
                        "response": response.text,
                    },
                )
                return None

            try:
                result = response.json()
            except Exception as e:
                logger.error(
                    "WayForPay API: failed to parse JSON response",
                    extra={"order_reference": order_reference, "error": str(e)},
                )
                return None

            # Verify response signature
            if "merchantSignature" in result:
                response_signature_fields = [
                    str(result.get("merchantAccount", "")),
                    str(result.get("orderReference", "")),
                    str(result.get("transactionStatus", "")),
                    str(result.get("reasonCode", "")),
                ]
                expected_signature = self._generate_signature(response_signature_fields)
                received_signature = str(result.get("merchantSignature", ""))

                if expected_signature.lower() != received_signature.lower():
                    logger.warning(
                        "WayForPay API response signature verification failed",
                        extra={"order_reference": order_reference},
                    )
                    return None

            return result

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Error checking payment status via WayForPay API: {e}",
                extra={"order_reference": order_reference},
                exc_info=True,
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error checking payment status: {e}",
                extra={"order_reference": order_reference},
                exc_info=True,
            )
            return None
