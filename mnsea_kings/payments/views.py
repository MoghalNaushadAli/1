import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from orders.models import Order
from .models import PaymentLog
from .utils import create_razorpay_order, verify_payment_signature, verify_webhook_signature, razorpay_configured

logger = logging.getLogger(__name__)


@login_required
def initiate_payment(request, order_number):
    """
    Renders the Razorpay Checkout page for an order. Used both right after
    placing a new "Pay Online" order, and as a "Pay Now" retry button from
    the order detail page if a previous payment attempt failed or was closed.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    if order.payment_method != "online":
        return redirect("orders:order_detail", order_number=order.order_number)

    if order.payment_status == "paid":
        messages.info(request, "This order is already paid.")
        return redirect("orders:order_detail", order_number=order.order_number)

    if not razorpay_configured():
        messages.error(
            request,
            "Online payments aren't set up yet on this site. Please choose Cash on Delivery, "
            "or contact us and we'll confirm your order manually.",
        )
        return redirect("orders:order_detail", order_number=order.order_number)

    # Reuse an existing Razorpay order if we already created one (e.g. user
    # closed the checkout popup and clicked "Pay Now" again) — Razorpay lets
    # you attempt multiple payments against the same order until it's paid.
    if not order.razorpay_order_id:
        try:
            rzp_order = create_razorpay_order(order)
        except Exception:
            logger.exception("Razorpay order creation failed for %s", order.order_number)
            messages.error(
                request,
                "We couldn't start the online payment right now. Please try again in a moment, "
                "or choose Cash on Delivery.",
            )
            return redirect("orders:order_detail", order_number=order.order_number)
        order.razorpay_order_id = rzp_order["id"]
        order.payment_status = "pending"
        order.save(update_fields=["razorpay_order_id", "payment_status"])
        PaymentLog.objects.create(
            order=order, event_type="razorpay_order_created",
            razorpay_order_id=order.razorpay_order_id, raw_payload=rzp_order,
        )

    context = {
        "order": order,
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "callback_url": request.build_absolute_uri(
            f"/payments/verify/{order.order_number}/"
        ),
    }
    return render(request, "payments/checkout_payment.html", context)


@login_required
@require_POST
def verify_payment(request, order_number):
    """
    Handles Razorpay's browser-side success callback. Verifies the HMAC
    signature (proves the payment really came from Razorpay and wasn't
    forged) before marking the order paid.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    razorpay_payment_id = request.POST.get("razorpay_payment_id", "")
    razorpay_order_id = request.POST.get("razorpay_order_id", "")
    razorpay_signature = request.POST.get("razorpay_signature", "")

    is_valid = verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)

    if is_valid and razorpay_order_id == order.razorpay_order_id:
        order.payment_status = "paid"
        order.razorpay_payment_id = razorpay_payment_id
        order.razorpay_signature = razorpay_signature
        order.paid_at = timezone.now()
        if order.status == "placed":
            order.status = "confirmed"
        order.save(update_fields=["payment_status", "razorpay_payment_id", "razorpay_signature", "paid_at", "status"])
        PaymentLog.objects.create(
            order=order, event_type="callback_verified",
            razorpay_order_id=razorpay_order_id, razorpay_payment_id=razorpay_payment_id,
        )
        messages.success(request, "Payment successful! Your order is confirmed.")
        return redirect("orders:order_success", order_number=order.order_number)

    PaymentLog.objects.create(
        order=order, event_type="callback_signature_invalid",
        razorpay_order_id=razorpay_order_id, razorpay_payment_id=razorpay_payment_id,
    )
    order.payment_status = "failed"
    order.save(update_fields=["payment_status"])
    messages.error(request, "We couldn't verify your payment. Please try again or choose Cash on Delivery.")
    return redirect("orders:order_detail", order_number=order.order_number)


@csrf_exempt
@require_POST
def razorpay_webhook(request):
    """
    Server-to-server webhook — the safety net for when a customer pays but
    closes the browser/app before the callback above fires. Configure this
    URL in the Razorpay Dashboard > Webhooks, subscribed to `payment.captured`
    and `payment.failed` events.
    """
    signature = request.headers.get("X-Razorpay-Signature", "")
    if not verify_webhook_signature(request.body, signature):
        logger.warning("Razorpay webhook signature verification failed.")
        return HttpResponse(status=400)

    try:
        payload = json.loads(request.body)
    except (ValueError, TypeError):
        return HttpResponse(status=400)

    event = payload.get("event", "")
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    razorpay_order_id = payment_entity.get("order_id", "")
    razorpay_payment_id = payment_entity.get("id", "")

    order = Order.objects.filter(razorpay_order_id=razorpay_order_id).first()

    if event == "payment.captured" and order:
        if order.payment_status != "paid":
            order.payment_status = "paid"
            order.razorpay_payment_id = razorpay_payment_id
            order.paid_at = timezone.now()
            if order.status == "placed":
                order.status = "confirmed"
            order.save(update_fields=["payment_status", "razorpay_payment_id", "paid_at", "status"])
        PaymentLog.objects.create(
            order=order, event_type="webhook_captured",
            razorpay_order_id=razorpay_order_id, razorpay_payment_id=razorpay_payment_id, raw_payload=payload,
        )
    elif event == "payment.failed" and order:
        order.payment_status = "failed"
        order.save(update_fields=["payment_status"])
        PaymentLog.objects.create(
            order=order, event_type="webhook_failed",
            razorpay_order_id=razorpay_order_id, razorpay_payment_id=razorpay_payment_id, raw_payload=payload,
        )

    return JsonResponse({"status": "ok"})
