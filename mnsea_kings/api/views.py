import logging
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from cart.models import CartItem
from catalog.models import Category, Product
from core.models import SiteConfig
from core.pricing import compute_totals
from orders.models import Address, Order, OrderItem
from payments.models import PaymentLog
from payments.utils import create_razorpay_order, verify_payment_signature, razorpay_configured

from .serializers import (
    AddressSerializer, CartItemSerializer, CategorySerializer, CheckoutSerializer,
    OrderSerializer, ProductSerializer, RegisterSerializer, SiteConfigSerializer, UserSerializer,
)


logger = logging.getLogger(__name__)


def _tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class RegisterView(generics.CreateAPIView):
    """POST /api/v1/auth/register/ — create account, returns JWT tokens right away."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"user": UserSerializer(user).data, **_tokens_for_user(user)},
            status=status.HTTP_201_CREATED,
        )


class MeView(generics.RetrieveAPIView):
    """GET /api/v1/auth/me/ — current logged-in user's profile."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# ---------------------------------------------------------------------------
# Catalog (public, read-only)
# ---------------------------------------------------------------------------
class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True).order_by("display_order", "name")
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Product.objects.filter(is_available=True).select_related("category")
        params = self.request.query_params

        category_slug = params.get("category")
        if category_slug:
            qs = qs.filter(category__slug=category_slug)

        query = params.get("q")
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(short_description__icontains=query) | Q(cut_info__icontains=query))

        if params.get("featured") == "true":
            qs = qs.filter(is_featured=True)
        if params.get("bestseller") == "true":
            qs = qs.filter(is_bestseller=True)

        sort = params.get("sort")
        if sort == "price_low":
            qs = qs.order_by("price")
        elif sort == "price_high":
            qs = qs.order_by("-price")
        elif sort == "name":
            qs = qs.order_by("name")

        return qs


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"


# ---------------------------------------------------------------------------
# Site config (public)
# ---------------------------------------------------------------------------
class SiteConfigView(generics.RetrieveAPIView):
    serializer_class = SiteConfigSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        return SiteConfig.load()


# ---------------------------------------------------------------------------
# Cart (authenticated, per-user, server-side — used by the mobile app)
# ---------------------------------------------------------------------------
class CartView(APIView):
    """
    GET  /api/v1/cart/  -> {items: [...], subtotal, delivery_fee, total, ...}
    POST /api/v1/cart/  -> {product_id, qty}  add/increment an item
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        items = CartItem.objects.filter(user=request.user).select_related("product", "product__category")
        subtotal = sum((i.line_total for i in items), Decimal("0.00"))
        totals = compute_totals(subtotal)
        return Response({
            "items": CartItemSerializer(items, many=True).data,
            **{k: v for k, v in totals.items()},
        })

    def post(self, request):
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data["product"]
        qty = serializer.validated_data.get("qty", 1)

        item, created = CartItem.objects.get_or_create(user=request.user, product=product, defaults={"qty": qty})
        if not created:
            item.qty += qty
            item.save(update_fields=["qty"])
        return Response(CartItemSerializer(item).data, status=status.HTTP_201_CREATED)


class CartItemDetailView(APIView):
    """
    PATCH  /api/v1/cart/items/<id>/  -> {qty}  set exact quantity
    DELETE /api/v1/cart/items/<id>/  -> remove item
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_item(self, request, pk):
        return get_object_or_404(CartItem, pk=pk, user=request.user)

    def patch(self, request, pk):
        item = self.get_item(request, pk)
        qty = request.data.get("qty")
        if qty is None or int(qty) < 1:
            return Response({"detail": "qty must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)
        item.qty = int(qty)
        item.save(update_fields=["qty"])
        return Response(CartItemSerializer(item).data)

    def delete(self, request, pk):
        self.get_item(request, pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Addresses
# ---------------------------------------------------------------------------
class AddressListCreateView(generics.ListCreateAPIView):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


# ---------------------------------------------------------------------------
# Checkout & payment (mirrors the website's orders/payments logic exactly,
# via the same models + core.pricing helper — no duplicated business rules)
# ---------------------------------------------------------------------------
class CheckoutView(APIView):
    """
    POST /api/v1/orders/checkout/
    Body: {address_id, delivery_slot, payment_method: "cod"|"online", notes}

    For payment_method="online" the response includes a Razorpay order_id +
    the public key_id + amount, which the mobile app hands straight to the
    Razorpay mobile SDK (React Native / Flutter) — that SDK shows the exact
    same UPI apps / cards / netbanking picker as the website's Checkout.js.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        cart_items = list(CartItem.objects.filter(user=request.user).select_related("product"))
        if not cart_items:
            return Response({"detail": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        address = get_object_or_404(Address, pk=data["address_id"], user=request.user)

        subtotal = sum((ci.line_total for ci in cart_items), Decimal("0.00"))
        config = SiteConfig.load()
        totals = compute_totals(subtotal, config)

        if totals["is_below_minimum"]:
            return Response(
                {"detail": f"Minimum order value is ₹{config.min_order_value}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment_method = data["payment_method"]

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                full_name=address.full_name,
                phone=address.phone,
                address_line=address.full_address,
                city=address.city,
                state=address.state,
                pincode=address.pincode,
                delivery_slot=data.get("delivery_slot", ""),
                payment_method=payment_method,
                payment_status="pending" if payment_method == "online" else "not_applicable",
                notes=data.get("notes", ""),
                subtotal=totals["subtotal"],
                delivery_fee=totals["delivery_fee"],
                total=totals["total"],
            )
            for ci in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=ci.product,
                    product_name=ci.product.name,
                    unit=ci.product.unit,
                    unit_price=ci.product.price,
                    qty=ci.qty,
                    line_total=ci.line_total,
                )
            CartItem.objects.filter(user=request.user).delete()

        response_data = {"order": OrderSerializer(order).data}

        if payment_method == "online":
            if not razorpay_configured():
                return Response(
                    {
                        "order": OrderSerializer(order).data,
                        "detail": "Online payments are not configured yet on the server. "
                                  "Order was created — please contact support or retry with Cash on Delivery.",
                    },
                    status=status.HTTP_201_CREATED,
                )
            try:
                rzp_order = create_razorpay_order(order)
            except Exception:
                logger.exception("Razorpay order creation failed for %s", order.order_number)
                return Response(
                    {
                        "order": OrderSerializer(order).data,
                        "detail": "Order created, but we couldn't start the online payment right now. "
                                  "Please retry payment shortly.",
                    },
                    status=status.HTTP_201_CREATED,
                )
            order.razorpay_order_id = rzp_order["id"]
            order.save(update_fields=["razorpay_order_id"])
            PaymentLog.objects.create(
                order=order, event_type="razorpay_order_created",
                razorpay_order_id=order.razorpay_order_id, raw_payload=rzp_order,
            )
            response_data["razorpay"] = {
                "key_id": settings.RAZORPAY_KEY_ID,
                "razorpay_order_id": order.razorpay_order_id,
                "amount": order.amount_in_paise,
                "currency": "INR",
            }

        return Response(response_data, status=status.HTTP_201_CREATED)


class VerifyPaymentView(APIView):
    """
    POST /api/v1/orders/verify-payment/
    Body: {order_number, razorpay_order_id, razorpay_payment_id, razorpay_signature}
    Called by the mobile app right after the Razorpay SDK reports success.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        order_number = request.data.get("order_number")
        razorpay_order_id = request.data.get("razorpay_order_id", "")
        razorpay_payment_id = request.data.get("razorpay_payment_id", "")
        razorpay_signature = request.data.get("razorpay_signature", "")

        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        is_valid = verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)

        if is_valid and razorpay_order_id == order.razorpay_order_id:
            order.payment_status = "paid"
            order.razorpay_payment_id = razorpay_payment_id
            order.razorpay_signature = razorpay_signature
            order.paid_at = timezone.now()
            if order.status == "placed":
                order.status = "confirmed"
            order.save(update_fields=["payment_status", "razorpay_payment_id", "razorpay_signature", "paid_at", "status"])
            PaymentLog.objects.create(
                order=order, event_type="callback_verified",
                razorpay_order_id=razorpay_order_id, razorpay_payment_id=razorpay_payment_id,
            )
            return Response({"detail": "Payment verified.", "order": OrderSerializer(order).data})

        order.payment_status = "failed"
        order.save(update_fields=["payment_status"])
        PaymentLog.objects.create(
            order=order, event_type="callback_signature_invalid",
            razorpay_order_id=razorpay_order_id, razorpay_payment_id=razorpay_payment_id,
        )
        return Response({"detail": "Payment verification failed."}, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Orders (history / detail)
# ---------------------------------------------------------------------------
class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "order_number"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
