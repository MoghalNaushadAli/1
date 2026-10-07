from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from catalog.models import Product
from core.models import SiteConfig
from core.pricing import compute_totals
from .cart import Cart


def cart_detail(request):
    cart = Cart(request)
    config = SiteConfig.load()
    totals = compute_totals(cart.get_subtotal(), config)
    context = {
        "cart": cart,
        "subtotal": totals["subtotal"],
        "delivery_fee": totals["delivery_fee"],
        "total": totals["total"],
        "config": config,
        "amount_to_free_delivery": totals["free_delivery_remaining"],
    }
    return render(request, "cart/cart_detail.html", context)


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_available=True)
    cart = Cart(request)
    qty = int(request.POST.get("qty", 1))
    cart.add(product, qty=qty)
    messages.success(request, f"Added {product.name} to your cart.")
    next_url = request.POST.get("next") or "cart:cart_detail"
    return redirect(next_url)


@require_POST
def cart_update(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    qty = int(request.POST.get("qty", 1))
    cart.add(product, qty=qty, replace=True)
    return redirect("cart:cart_detail")


@require_POST
def cart_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.remove(product)
    messages.info(request, f"Removed {product.name} from your cart.")
    return redirect("cart:cart_detail")
