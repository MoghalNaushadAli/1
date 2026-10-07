from django.contrib import admin
from .models import PaymentLog


@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ("event_type", "order", "razorpay_order_id", "razorpay_payment_id", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("razorpay_order_id", "razorpay_payment_id", "order__order_number")
    readonly_fields = ("order", "event_type", "razorpay_order_id", "razorpay_payment_id", "raw_payload", "created_at")

    def has_add_permission(self, request):
        return False
