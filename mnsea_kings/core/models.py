from django.db import models


class SiteConfig(models.Model):
    """
    Singleton model holding site-wide settings the owner (brother) can
    edit from the Django admin without touching any code — e.g. delivery
    fee, free-delivery threshold, contact details, UPI id, banner text.
    """
    site_name = models.CharField(max_length=100, default="MNSEA KINGS CORPORATION")
    tagline = models.CharField(max_length=200, default="Fresh Seafood. Quality Meat. Fast Delivery.")
    banner_message = models.CharField(
        max_length=250,
        blank=True,
        default="Free delivery on orders above ₹999 | Fresh cut & delivered same day",
        help_text="Scrolling/top banner message shown on every page.",
    )
    contact_phone = models.CharField(max_length=20, default="+91 90000 00000")
    contact_whatsapp = models.CharField(max_length=20, blank=True, default="+91 90000 00000")
    contact_email = models.EmailField(default="orders@mnseakings.in")
    upi_id = models.CharField(max_length=100, blank=True, default="mnseakings@upi")
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=49.00)
    free_delivery_above = models.DecimalField(max_digits=8, decimal_places=2, default=999.00)
    min_order_value = models.DecimalField(max_digits=8, decimal_places=2, default=299.00)
    gst_percent = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    instagram_url = models.URLField(blank=True, default="")
    facebook_url = models.URLField(blank=True, default="")

    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configuration"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        self.pk = 1  # enforce singleton
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
