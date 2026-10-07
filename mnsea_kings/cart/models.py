from django.conf import settings
from django.db import models


class CartItem(models.Model):
    """
    Server-side, per-user cart used by the mobile app (and any future API
    client). The website continues to use the lightweight session-based
    `Cart` class in cart.py for guest browsing — this model is additive and
    doesn't change that. Logged-in mobile users get a durable cart that
    survives app restarts / device changes.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="+")
    qty = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user} — {self.product} x{self.qty}"

    @property
    def line_total(self):
        return self.product.price * self.qty
