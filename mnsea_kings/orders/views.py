from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from cart.cart import Cart
from core.models import SiteConfig
from core.pricing import compute_totals
from payments.utils import razorpay_configured
from .forms import AddressForm, CheckoutForm
from .models import Address, Order, OrderItem


@login_required
def address_book(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Address saved.")
            return redirect("orders:checkout")
    else:
        form = AddressForm()
    addresses = Address.objects.filter(user=request.user)
    return render(request, "orders/address_book.html", {"form": form, "addresses": addresses})


@login_required
def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Your cart is empty. Add some fresh items first!")
        return redirect("catalog:product_list")

    config = SiteConfig.load()
    totals = compute_totals(cart.get_subtotal(), config)
    subtotal, delivery_fee, total = totals["subtotal"], totals["delivery_fee"], totals["total"]

    if totals["is_below_minimum"]:
        messages.warning(
            request,
            f"Minimum order value is {settings_currency()}{config.min_order_value}. "
            f"Please add items worth {settings_currency()}{config.min_order_value - subtotal} more.",
        )
        return redirect("cart:cart_detail")

    addresses = Address.objects.filter(user=request.user)
    if request.method == "POST":
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            address = form.cleaned_data.get("address")
            if not address:
                messages.error(request, "Please select or add a delivery address.")
                return redirect("orders:address_book")

            payment_method = form.cleaned_data["payment_method"]
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    full_name=address.full_name,
                    phone=address.phone,
                    address_line=address.full_address,
                    city=address.city,
                    state=address.state,
                    pincode=address.pincode,
                    delivery_slot=form.cleaned_data["delivery_slot"],
                    payment_method=payment_method,
                    payment_status="pending" if payment_method == "online" else "not_applicable",
                    notes=form.cleaned_data.get("notes", ""),
                    subtotal=subtotal,
                    delivery_fee=delivery_fee,
                    total=total,
                )
                for line in cart:
                    OrderItem.objects.create(
                        order=order,
                        product=line["product"],
                        product_name=line["product"].name,
                        unit=line["product"].unit,
                        unit_price=line["unit_price"],
                        qty=line["qty"],
                        line_total=line["line_total"],
                    )
                cart.clear()

            if payment_method == "online":
                # Send them to Razorpay Checkout (UPI apps, cards, netbanking) —
                # order is only marked "confirmed" once payment is verified.
                return redirect("payments:initiate_payment", order_number=order.order_number)
            return redirect("orders:order_success", order_number=order.order_number)
    else:
        form = CheckoutForm(user=request.user)

    context = {
        "form": form,
        "addresses": addresses,
        "cart": cart,
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "total": total,
        "config": config,
        "razorpay_enabled": razorpay_configured(),
    }
    return render(request, "orders/checkout.html", context)


def settings_currency():
    from django.conf import settings
    return getattr(settings, "CURRENCY_SYMBOL", "₹")


@login_required
def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, "orders/order_success.html", {"order": order})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, "orders/order_history.html", {"orders": orders})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, "orders/order_detail.html", {"order": order})
