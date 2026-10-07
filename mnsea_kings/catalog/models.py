from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    icon_emoji = models.CharField(
        max_length=10, blank=True, default="🐟",
        help_text="Small emoji shown next to the category, e.g. 🐟 🦐 🍗 🐐"
    )
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:category_detail", args=[self.slug])


UNIT_CHOICES = [
    ("kg", "per kg"),
    ("500g", "per 500g"),
    ("250g", "per 250g"),
    ("piece", "per piece"),
    ("dozen", "per dozen"),
    ("pack", "per pack"),
]


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=150)
    icon_emoji = models.CharField(
        max_length=10,
        blank=True,
        default="🐟",
        help_text="Product icon shown when no product photo is uploaded.",
    )
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    short_description = models.CharField(max_length=250, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="products/", blank=True, null=True)

    # --- Pricing: owner edits these daily from the admin list view ---
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default="kg")
    price = models.DecimalField(max_digits=8, decimal_places=2, help_text="Today's selling price")
    mrp = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True,
        help_text="Optional strike-through price to show a discount"
    )
    price_updated_at = models.DateTimeField(auto_now=True)

    is_available = models.BooleanField(default=True, help_text="Uncheck when out of stock")
    is_featured = models.BooleanField(default=False, help_text="Show on homepage 'Today's Catch' section")
    is_bestseller = models.BooleanField(default=False)
    cut_info = models.CharField(
        max_length=150, blank=True,
        help_text="e.g. 'Cleaned & Curry Cut', 'Whole, Descaled', 'Boneless'"
    )
    origin = models.CharField(max_length=100, blank=True, help_text="e.g. 'Kakinada Coast', 'Farm Fresh'")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_featured", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_unit_display()})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            i = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base_slug}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:product_detail", args=[self.slug])

    @property
    def discount_percent(self):
        if self.mrp and self.mrp > self.price:
            return round((self.mrp - self.price) / self.mrp * 100)
        return 0
