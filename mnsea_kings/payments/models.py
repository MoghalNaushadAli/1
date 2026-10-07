from django.db import models


class PaymentLog(models.Model):
    """
    Audit trail of everything that happens around a payment — order creation
    at Razorpay, browser-side callback verification, and server-to-server
    webhook events. Handy for the business owner / support to debug "I paid
    but order still shows pending" type queries.
    """
    EVENT_CHOICES = [
        ("razorpay_order_created", "Razorpay Order Created"),
        ("callback_verified", "Payment Verified (Browser Callback)"),
        ("callback_signature_invalid", "Signature Verification Failed (Browser Callback)"),
        ("webhook_captured", "Webhook: Payment Captured"),
        ("webhook_failed", "Webhook: Payment Failed"),
        ("webhook_signature_invalid", "Webhook Signature Invalid"),
    ]

    order = models.ForeignKey(
        "orders.Order", on_delete=models.CASCADE, related_name="payment_logs", null=True, blank=True
    )
    event_type = models.CharField(max_length=40, choices=EVENT_CHOICES)
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    raw_payload = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_event_type_display()} — {self.razorpay_order_id or self.order_id}"
