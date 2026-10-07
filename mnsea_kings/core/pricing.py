"""
Single source of truth for order-total calculations (delivery fee, free-delivery
threshold, grand total). Used by the website cart/checkout views AND the mobile
REST API, so pricing logic never has to be written twice or drift out of sync.
"""
from decimal import Decimal
from .models import SiteConfig


def compute_totals(subtotal: Decimal, config: SiteConfig = None):
    """
    Returns a dict: subtotal, delivery_fee, total, free_delivery_remaining,
    min_order_value, is_below_minimum.
    """
    config = config or SiteConfig.load()
    subtotal = Decimal(subtotal or 0)

    if subtotal <= 0:
        delivery_fee = Decimal("0.00")
    elif subtotal >= config.free_delivery_above:
        delivery_fee = Decimal("0.00")
    else:
        delivery_fee = config.delivery_fee

    total = subtotal + delivery_fee
    free_delivery_remaining = max(config.free_delivery_above - subtotal, Decimal("0.00"))
    is_below_minimum = Decimal("0.00") < subtotal < config.min_order_value

    return {
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "total": total,
        "free_delivery_remaining": free_delivery_remaining,
        "min_order_value": config.min_order_value,
        "is_below_minimum": is_below_minimum,
    }
