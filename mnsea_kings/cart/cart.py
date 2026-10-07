from decimal import Decimal
from catalog.models import Product

CART_SESSION_KEY = "cart"


class Cart:
    """
    Simple session-based cart. Prices are always pulled live from the
    Product table (not frozen at add-to-cart time) since this business
    changes prices day to day — the cart/checkout always reflects
    today's price set by the owner in the admin.
    """

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if cart is None:
            cart = self.session[CART_SESSION_KEY] = {}
        self.cart = cart

    def add(self, product, qty=1, replace=False):
        pid = str(product.id)
        if pid not in self.cart:
            self.cart[pid] = {"qty": 0}
        if replace:
            self.cart[pid]["qty"] = qty
        else:
            self.cart[pid]["qty"] += qty
        if self.cart[pid]["qty"] <= 0:
            self.remove(product)
        self.save()

    def remove(self, product):
        pid = str(product.id)
        if pid in self.cart:
            del self.cart[pid]
            self.save()

    def save(self):
        self.session.modified = True

    def clear(self):
        self.session[CART_SESSION_KEY] = {}
        self.save()

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        products_map = {str(p.id): p for p in products}
        for pid, item in self.cart.items():
            product = products_map.get(pid)
            if not product:
                continue
            line_total = product.price * item["qty"]
            yield {
                "product": product,
                "qty": item["qty"],
                "unit_price": product.price,
                "line_total": line_total,
            }

    def __len__(self):
        return sum(item["qty"] for item in self.cart.values())

    def get_subtotal(self):
        return sum((line["line_total"] for line in self), Decimal("0.00"))
