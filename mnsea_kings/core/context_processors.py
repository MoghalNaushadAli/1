from django.conf import settings
from .models import SiteConfig
from catalog.models import Category


def site_context(request):
    """Makes site config + categories + live cart count available in every template."""
    cart = request.session.get("cart", {})
    cart_count = sum(item.get("qty", 0) for item in cart.values())
    return {
        "site_config": SiteConfig.load(),
        "nav_categories": Category.objects.filter(is_active=True).order_by("display_order", "name"),
        "cart_count": cart_count,
        # razorpay key_id is PUBLIC (safe in HTML/JS) — the secret key never leaves the server
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "razorpay_enabled": bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET),
    }
