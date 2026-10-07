from django.contrib import admin
from .models import CartItem


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Read-only view into mobile app users' active carts — useful for support/debugging."""
    list_display = ("user", "product", "qty", "updated_at")
    search_fields = ("user__username", "product__name")
    readonly_fields = ("user", "product", "qty", "added_at", "updated_at")

    def has_add_permission(self, request):
        return False
