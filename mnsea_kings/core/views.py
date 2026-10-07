from django.shortcuts import render
from catalog.models import Category, Product


def home(request):
    featured = Product.objects.filter(is_available=True, is_featured=True)[:8]
    bestsellers = Product.objects.filter(is_available=True, is_bestseller=True)[:8]
    categories = Category.objects.filter(is_active=True)
    context = {
        "featured": featured,
        "bestsellers": bestsellers,
        "categories": categories,
    }
    return render(request, "core/home.html", context)


def about(request):
    return render(request, "core/about.html")


def contact(request):
    return render(request, "core/contact.html")
