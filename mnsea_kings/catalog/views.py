from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404

from .models import Category, Product


def product_list(request):
    """All products, with optional category filter (?category=slug) and search (?q=...)."""
    products = Product.objects.filter(is_available=True).select_related("category")
    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "")
    active_category = None

    if category_slug:
        active_category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products = products.filter(category=active_category)

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(short_description__icontains=query) | Q(cut_info__icontains=query)
        )

    sort = request.GET.get("sort", "")
    if sort == "price_low":
        products = products.order_by("price")
    elif sort == "price_high":
        products = products.order_by("-price")
    elif sort == "name":
        products = products.order_by("name")

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "categories": Category.objects.filter(is_active=True),
        "active_category": active_category,
        "query": query,
        "sort": sort,
    }
    return render(request, "catalog/product_list.html", context)


def category_detail(request, slug):
    request.GET = request.GET.copy()
    request.GET["category"] = slug
    return product_list(request)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related = Product.objects.filter(category=product.category, is_available=True).exclude(pk=product.pk)[:4]
    return render(request, "catalog/product_detail.html", {"product": product, "related": related})
