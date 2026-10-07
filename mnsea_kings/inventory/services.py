from django.db import transaction
from django.utils import timezone

from .models import StockDay, StockTransaction


@transaction.atomic
def sync_order_transactions(order):
    """Create idempotent sale and return movements for every order item."""
    if not order.pk:
        return
    active = order.status != "cancelled" and order.payment_status != "refunded"
    for item in order.items.select_related("product"):
        if item.product_id is None:
            continue
        sale_key = f"order:{order.pk}:item:{item.pk}:sale"
        return_key = f"order:{order.pk}:item:{item.pk}:customer-return"
        if active:
            if not StockTransaction.objects.filter(source_key=sale_key).exists():
                stock_day = StockDay.objects.filter(date=order.placed_at.date()).first()
                if stock_day:
                    line = stock_day.lines.filter(product=item.product).first()
                    if line and line.closing_qty < item.qty:
                        raise ValueError(
                            f"Insufficient stock for {item.product.name}: "
                            f"{line.closing_qty} available, {item.qty} requested."
                        )
                StockTransaction.objects.create(
                    source_key=sale_key,
                    product=item.product,
                    transaction_type="sale",
                    quantity=item.qty,
                    transaction_date=order.placed_at.date() if order.placed_at else timezone.localdate(),
                    reason=f"Order {order.order_number}",
                    order=order,
                )
            StockTransaction.objects.filter(source_key=return_key).delete()
        elif StockTransaction.objects.filter(source_key=sale_key).exists():
            StockTransaction.objects.get_or_create(
                source_key=return_key,
                defaults={
                    "product": item.product,
                    "transaction_type": "customer_return",
                    "quantity": item.qty,
                    "transaction_date": timezone.localdate(),
                    "reason": f"Cancelled/refunded order {order.order_number}",
                    "order": order,
                },
            )