from django.contrib import admin
from .models import Address, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "unit", "unit_price", "qty", "line_total")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number", "full_name", "phone", "city", "total",
        "payment_method", "payment_status", "status", "placed_at",
    )
    list_editable = ("status",)
    list_filter = ("status", "payment_method", "payment_status", "placed_at")
    search_fields = ("order_number", "full_name", "phone", "pincode", "razorpay_order_id", "razorpay_payment_id")
    readonly_fields = (
        "order_number", "subtotal", "delivery_fee", "total", "placed_at", "updated_at",
        "razorpay_order_id", "razorpay_payment_id", "razorpay_signature", "paid_at",
    )
    inlines = [OrderItemInline]
    date_hierarchy = "placed_at"


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "city", "pincode", "phone", "is_default")
    search_fields = ("full_name", "phone", "city", "pincode")
