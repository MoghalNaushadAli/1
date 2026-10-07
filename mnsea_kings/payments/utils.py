"""
Razorpay integration helpers.

Razorpay's standard Checkout widget natively supports ALL of these in one
integration — no separate SDK per app needed:
  - UPI: intent flow (deep-links straight into GPay / PhonePe / Paytm / BHIM
    / any UPI app installed on the phone), UPI collect (enter VPA), and UPI QR
  - Cards: Visa, Mastercard, RuPay, Amex — credit & debit
  - Netbanking: all major Indian banks
  - Wallets & Pay Later options

So wiring up Razorpay once == wiring up "every UPI app, GPay, PhonePe, cards"
automatically. This module wraps the 3 things we need: create an order,
verify the browser-side payment callback, and verify server-side webhooks.
"""
import hashlib
import hmac
import logging

import razorpay
from django.conf import settings

logger = logging.getLogger(__name__)


def razorpay_configured() -> bool:
    return bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)


def get_client():
    if not razorpay_configured():
        return None
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_razorpay_order(order):
    """
    Creates a Razorpay Order for our local `Order` instance and returns the
    Razorpay order dict (contains its own `id`). Amount must be in paise.
    """
    client = get_client()
    if client is None:
        raise RuntimeError(
            "Razorpay is not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET "
            "environment variables (see README) to enable online payments."
        )
    payload = {
        "amount": order.amount_in_paise,
        "currency": "INR",
        "receipt": order.order_number,
        "notes": {
            "order_number": order.order_number,
            "customer": order.full_name,
            "phone": order.phone,
        },
    }
    return client.order.create(data=payload)


def verify_payment_signature(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
    """Verify the signature Razorpay sends back to the browser after a successful checkout."""
    if not razorpay_configured():
        return False
    message = f"{razorpay_order_id}|{razorpay_payment_id}"
    generated_signature = hmac.new(
        key=settings.RAZORPAY_KEY_SECRET.encode(),
        msg=message.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(generated_signature, razorpay_signature or "")


def verify_webhook_signature(raw_body: bytes, received_signature: str) -> bool:
    """Verify a Razorpay webhook payload using the separate Webhook Secret (set in Razorpay dashboard)."""
    if not settings.RAZORPAY_WEBHOOK_SECRET:
        return False
    generated_signature = hmac.new(
        key=settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(generated_signature, received_signature or "")
