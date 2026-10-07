from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "icon_emoji", "display_order", "is_active")
    list_editable = ("display_order", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # price/mrp/is_available are list_editable so the owner can update
    # today's prices for many products at once, right from the list page.
    list_display = (
        "name", "category", "icon_emoji", "unit", "price", "mrp",
        "is_available", "is_featured", "is_bestseller", "price_updated_at",
    )
    list_editable = ("icon_emoji", "price", "mrp", "is_available", "is_featured", "is_bestseller")
    list_filter = ("category", "is_available", "is_featured", "unit")
    search_fields = ("name", "short_description")
    prepopulated_fields = {"slug": ("name",)}
    list_per_page = 50
