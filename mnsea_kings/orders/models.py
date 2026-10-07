from django.conf import settings
from django.db import models


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15)
    line1 = models.CharField(max_length=200)
    line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    landmark = models.CharField(max_length=150, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.full_name}, {self.city} - {self.pincode}"

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @property
    def full_address(self):
        parts = [self.line1, self.line2, self.landmark, self.city, self.state, self.pincode]
        return ", ".join(p for p in parts if p)


PAYMENT_CHOICES = [
    ("cod", "Cash on Delivery"),
    ("online", "UPI / Cards / Netbanking (Pay Online)"),
]

PAYMENT_STATUS_CHOICES = [
    ("not_applicable", "Cash on Delivery"),
    ("pending", "Payment Pending"),
    ("paid", "Paid"),
    ("failed", "Payment Failed"),
    ("refunded", "Refunded"),
]

STATUS_CHOICES = [
    ("placed", "Order Placed"),
    ("confirmed", "Confirmed"),
    ("packed", "Packed"),
    ("out_for_delivery", "Out for Delivery"),
    ("delivered", "Delivered"),
    ("cancelled", "Cancelled"),
]


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    order_number = models.CharField(max_length=20, unique=True, blank=True)

    # Snapshot of the delivery address at the time of order (so later edits
    # to the saved address book don't change historical orders)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15)
    address_line = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)

    delivery_slot = models.CharField(max_length=100, blank=True, help_text="e.g. Tomorrow, 8 AM - 10 AM")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default="cod")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="placed")
    notes = models.CharField(max_length=250, blank=True)

    # --- Razorpay payment tracking (covers UPI apps like GPay/PhonePe/Paytm/BHIM,
    # debit/credit cards, netbanking & wallets — all through one Razorpay Checkout) ---
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="not_applicable")
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    placed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-placed_at"]

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and not self.order_number:
            self.order_number = f"MNSK{self.placed_at.strftime('%y%m%d')}{self.pk:04d}"
            super().save(update_fields=["order_number"])

    @property
    def needs_payment(self):
        """True when this is an online-payment order that hasn't been paid yet."""
        return self.payment_method == "online" and self.payment_status in ("pending", "failed")

    @property
    def amount_in_paise(self):
        """Razorpay's API expects amounts in the smallest currency unit (paise for INR)."""
        return int(self.total * 100)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("catalog.Product", on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=150)
    unit = models.CharField(max_length=10)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    qty = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} x{self.qty}"
