from calendar import month_name
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from catalog.models import Product


class StockMonth(models.Model):
    year = models.PositiveIntegerField()
    month = models.PositiveSmallIntegerField(choices=[(i, month_name[i]) for i in range(1, 13)])
    is_closed = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_stock_months")
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-year", "-month"]
        constraints = [
            models.UniqueConstraint(fields=("year", "month"), name="unique_stock_month"),
        ]
        verbose_name = "Monthly Stock Book"
        verbose_name_plural = "Monthly Stock Books"

    def __str__(self):
        return f"{month_name[self.month]} {self.year}" + (" (Closed)" if self.is_closed else "")

    @property
    def first_day(self):
        return date(self.year, self.month, 1)

    @property
    def last_day(self):
        if self.month == 12:
            return date(self.year + 1, 1, 1)
        return date(self.year, self.month + 1, 1)

    def close(self):
        from django.utils import timezone
        self.is_closed = True
        self.closed_at = timezone.now()
        self.save(update_fields=["is_closed", "closed_at"])

    def approve(self, user):
        from django.utils import timezone
        self.is_approved = True
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save(update_fields=["is_approved", "approved_by", "approved_at"])


TRANSACTION_TYPES = [
    ("purchase", "Purchase / Received"),
    ("sale", "Sale"),
    ("customer_return", "Customer Return"),
    ("supplier_return", "Supplier Return"),
    ("wastage", "Wastage"),
    ("adjustment", "Manual Adjustment"),
]


class StockTransaction(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stock_transactions")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    transaction_date = models.DateField()
    reason = models.CharField(max_length=250, blank=True)
    order = models.ForeignKey("orders.Order", on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_transactions")
    source_key = models.CharField(max_length=150, unique=True, null=True, blank=True)
    created_by = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-transaction_date", "-created_at"]

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.product.name} ({self.quantity})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.quantity <= 0:
            raise ValidationError({"quantity": "Quantity must be greater than zero."})
        if self.transaction_type == "adjustment" and not self.reason.strip():
            raise ValidationError({"reason": "A reason is required for manual adjustments."})

    @property
    def signed_quantity(self):
        if self.transaction_type in ("sale", "supplier_return", "wastage"):
            return -self.quantity
        return self.quantity

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class StockDay(models.Model):
    stock_month = models.ForeignKey(StockMonth, on_delete=models.CASCADE, related_name="days")
    date = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["date"]
        constraints = [
            models.UniqueConstraint(fields=("stock_month", "date"), name="unique_stock_day"),
        ]

    def __str__(self):
        return f"{self.stock_month} - {self.date:%d %b %Y}"

    def clean(self):
        if self.stock_month_id and not (self.stock_month.first_day <= self.date < self.stock_month.last_day):
            raise ValidationError("The stock day must belong to its selected month.")

    @property
    def previous_day(self):
        return self.stock_month.days.filter(date__lt=self.date).order_by("-date").first()


class StockLine(models.Model):
    day = models.ForeignKey(StockDay, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stock_lines")
    opening_qty = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0"))
    received_qty = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0"))
    sold_qty = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0"))
    returns_qty = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0"))
    wastage_qty = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0"))
    remarks = models.CharField(max_length=250, blank=True)

    class Meta:
        ordering = ["product__category__display_order", "product__name"]
        constraints = [
            models.UniqueConstraint(fields=("day", "product"), name="unique_stock_line_product_day"),
        ]

    def __str__(self):
        return f"{self.day.date:%d %b} - {self.product.name}"

    @property
    def closing_qty(self):
        return self.opening_qty + self.received_qty + self.effective_returns_qty - self.effective_sold_qty - self.wastage_qty

    @property
    def automatic_sold_qty(self):
        return sum(
            (transaction.quantity for transaction in self.product.stock_transactions.filter(
                transaction_date=self.day.date, transaction_type="sale"
            )),
            Decimal("0"),
        )

    @property
    def automatic_returns_qty(self):
        return sum(
            (transaction.quantity for transaction in self.product.stock_transactions.filter(
                transaction_date=self.day.date, transaction_type="customer_return"
            )),
            Decimal("0"),
        )

    @property
    def effective_sold_qty(self):
        return self.sold_qty + self.automatic_sold_qty

    @property
    def effective_returns_qty(self):
        return self.returns_qty + self.automatic_returns_qty

    @property
    def category_name(self):
        return self.product.category.name

    def carried_forward_opening(self):
        previous_line = (
            StockLine.objects.filter(
                product=self.product,
                day__date__lt=self.day.date,
            )
            .select_related("day")
            .order_by("-day__date")
            .first()
        )
        return previous_line.closing_qty if previous_line else Decimal("0")

    def save(self, *args, **kwargs):
        if self.day.stock_month.is_closed:
            raise ValidationError("A closed stock month cannot be edited.")
        self.opening_qty = self.carried_forward_opening()
        super().save(*args, **kwargs)
