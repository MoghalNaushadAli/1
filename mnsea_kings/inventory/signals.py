from django.db.models.signals import post_save
from django.dispatch import receiver

from orders.models import Order, OrderItem

from .services import sync_order_transactions


@receiver(post_save, sender=Order)
def order_saved(sender, instance, **kwargs):
    sync_order_transactions(instance)


@receiver(post_save, sender=OrderItem)
def order_item_saved(sender, instance, **kwargs):
    sync_order_transactions(instance.order)