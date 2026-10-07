from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect

from orders.models import Address, Order
from .forms import RegisterForm


def register(request):
    if request.user.is_authenticated:
        return redirect("core:home")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to MNSEA KINGS, {user.first_name}! Your account is ready.")
            return redirect("core:home")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    addresses = Address.objects.filter(user=request.user)
    recent_orders = Order.objects.filter(user=request.user)[:5]
    return render(request, "accounts/profile.html", {"addresses": addresses, "recent_orders": recent_orders})
