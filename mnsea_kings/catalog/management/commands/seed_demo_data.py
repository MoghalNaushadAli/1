from django.core.management.base import BaseCommand
from catalog.models import Category, Product
from core.models import SiteConfig


CATEGORIES = [
    {"name": "Fish", "icon_emoji": "🐟", "display_order": 1},
    {"name": "Prawns", "icon_emoji": "🦐", "display_order": 2},
    {"name": "Chicken", "icon_emoji": "🍗", "display_order": 3},
    {"name": "Mutton", "icon_emoji": "🐐", "display_order": 4},
    {"name": "Other Seafood", "icon_emoji": "🦑", "display_order": 5},
]

PRODUCTS = [
    # Fish
    dict(category="Fish", name="Rohu (Curry Cut)", unit="kg", price=280, mrp=320,
         cut_info="Cleaned & Curry Cut", origin="Andhra Coast", is_featured=True, is_bestseller=True,
         short_description="Fresh water Rohu, cleaned and cut for curry."),
    dict(category="Fish", name="Pomfret (Whole, Silver)", unit="kg", price=650, mrp=720,
         cut_info="Whole, Descaled & Gutted", origin="Kakinada Coast", is_featured=True,
         short_description="Premium silver pomfret, great for frying."),
    dict(category="Fish", name="Vanjaram (Seer Fish Slices)", unit="kg", price=850,
         cut_info="Steak Cut", origin="Visakhapatnam Coast", is_bestseller=True,
         short_description="Boneless seer fish steaks, ideal for fry & curry."),
    dict(category="Fish", name="Katla (Curry Cut)", unit="kg", price=260,
         cut_info="Cleaned & Curry Cut", origin="Local Freshwater Farms",
         short_description="Soft-textured Katla, cut for everyday curries."),
    dict(category="Fish", name="Tilapia (Whole Cleaned)", unit="kg", price=220,
         cut_info="Whole, Cleaned", origin="Farm Fresh",
         short_description="Mild-flavoured tilapia, cleaned and ready to cook."),
    # Prawns
    dict(category="Prawns", name="Tiger Prawns (Medium)", unit="500g", price=380, mrp=420,
         cut_info="Peeled & Deveined", origin="Kakinada Coast", is_featured=True, is_bestseller=True,
         short_description="Juicy tiger prawns, peeled and deveined for easy cooking."),
    dict(category="Prawns", name="Jumbo Prawns (King Size)", unit="500g", price=650,
         cut_info="Head-on, Shell-on", origin="Deep Sea Catch", is_featured=True,
         short_description="Extra-large king prawns, perfect for grilling & tandoori."),
    dict(category="Prawns", name="Small Prawns (Chinnala Royyalu)", unit="500g", price=260,
         cut_info="Cleaned", origin="Local Coast",
         short_description="Small prawns, great for fry and pulusu."),
    # Chicken
    dict(category="Chicken", name="Chicken Curry Cut (Skinless)", unit="kg", price=230, mrp=260,
         cut_info="Skinless, Curry Cut", origin="Farm Fresh", is_featured=True, is_bestseller=True,
         short_description="Tender skinless chicken, cut for curries."),
    dict(category="Chicken", name="Chicken Boneless", unit="kg", price=310,
         cut_info="100% Boneless", origin="Farm Fresh", is_bestseller=True,
         short_description="Clean boneless chicken breast & thigh mix."),
    dict(category="Chicken", name="Chicken Drumsticks", unit="kg", price=260,
         cut_info="Whole Drumsticks", origin="Farm Fresh",
         short_description="Juicy drumsticks, perfect for grilling & frying."),
    dict(category="Chicken", name="Chicken Lollipop", unit="kg", price=340,
         cut_info="Ready to Cook", origin="Farm Fresh",
         short_description="Frenched drumettes, ready for your favourite starter."),
    dict(category="Chicken", name="Country Chicken (Naatu Kodi)", unit="kg", price=520,
         cut_info="Curry Cut", origin="Free-range Farms", is_featured=True,
         short_description="Free-range country chicken, rich flavour for curries."),
    # Mutton
    dict(category="Mutton", name="Mutton Curry Cut", unit="kg", price=780, mrp=850,
         cut_info="Bone-in, Curry Cut", origin="Farm Fresh", is_featured=True, is_bestseller=True,
         short_description="Tender goat meat, bone-in, cut for curry."),
    dict(category="Mutton", name="Mutton Boneless", unit="kg", price=920,
         cut_info="100% Boneless", origin="Farm Fresh",
         short_description="Premium boneless mutton for rich gravies."),
    dict(category="Mutton", name="Mutton Liver & Offal", unit="500g", price=220,
         cut_info="Cleaned", origin="Farm Fresh",
         short_description="Fresh mutton liver, kidney & offal mix."),
    # Other Seafood
    dict(category="Other Seafood", name="Squid Rings (Kanava)", unit="500g", price=340,
         cut_info="Cleaned, Rings Cut", origin="Deep Sea Catch", is_featured=True,
         short_description="Tender squid rings, ready for fry or curry."),
    dict(category="Other Seafood", name="Crab (Sea Crab, Medium)", unit="kg", price=480,
         cut_info="Live/Fresh, Cleaned", origin="Coastal Catch",
         short_description="Fresh sea crab, great for spicy crab curry."),
    dict(category="Other Seafood", name="Mussels (Cleaned)", unit="500g", price=210,
         cut_info="Cleaned & Shelled", origin="Coastal Catch",
         short_description="Fresh mussels, cleaned and ready to cook."),
]


class Command(BaseCommand):
    help = "Seed the database with demo categories, products and site configuration for MNSEA KINGS CORPORATION."

    def handle(self, *args, **options):
        SiteConfig.load()
        self.stdout.write(self.style.SUCCESS("Site configuration ready."))

        cat_map = {}
        for c in CATEGORIES:
            obj, created = Category.objects.get_or_create(name=c["name"], defaults=c)
            cat_map[c["name"]] = obj
            self.stdout.write(f"  Category: {obj.name} {'(created)' if created else '(exists)'}")

        created_count = 0
        for p in PRODUCTS:
            cat_name = p.pop("category")
            category = cat_map[cat_name]
            obj, created = Product.objects.get_or_create(
                name=p["name"], defaults={**p, "category": category}
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done! {created_count} new products added. Total products: {Product.objects.count()}"
        ))
        self.stdout.write(self.style.WARNING(
            "Reminder: product images are placeholders (none) — upload real photos from the admin panel, "
            "and update prices daily from Catalog > Products (price is an editable column)."
        ))
