from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from accounts.models import Profile
from cart.models import CartItem
from catalog.models import Category, Product
from core.models import SiteConfig
from orders.models import Address, Order, OrderItem


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    phone = serializers.CharField(write_only=True, required=True, max_length=15)

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "email", "password", "phone"]

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def create(self, validated_data):
        phone = validated_data.pop("phone")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        Profile.objects.create(user=user, phone=phone)
        return user


class UserSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source="profile.phone", read_only=True, default="")

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "email", "phone"]


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon_emoji", "display_order"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category", write_only=True, required=False
    )
    unit_display = serializers.CharField(source="get_unit_display", read_only=True)
    image = serializers.ImageField(read_only=True, use_url=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "category", "category_id", "short_description", "description",
            "image", "unit", "unit_display", "price", "mrp", "discount_percent",
            "is_available", "is_featured", "is_bestseller", "cut_info", "origin",
        ]


# ---------------------------------------------------------------------------
# Cart (server-side, per authenticated user — used by the mobile app)
# ---------------------------------------------------------------------------
class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_available=True), source="product", write_only=True
    )
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id", "qty", "line_total"]

    def validate_qty(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------
class AddressSerializer(serializers.ModelSerializer):
    full_address = serializers.CharField(read_only=True)

    class Meta:
        model = Address
        fields = [
            "id", "full_name", "phone", "line1", "line2", "landmark",
            "city", "state", "pincode", "is_default", "full_address",
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "unit", "unit_price", "qty", "line_total"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    payment_method_display = serializers.CharField(source="get_payment_method_display", read_only=True)
    payment_status_display = serializers.CharField(source="get_payment_status_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "order_number", "full_name", "phone", "address_line", "city", "state", "pincode",
            "delivery_slot", "payment_method", "payment_method_display",
            "payment_status", "payment_status_display", "status", "status_display", "notes",
            "subtotal", "delivery_fee", "total", "placed_at", "updated_at", "items",
        ]
        read_only_fields = fields


class CheckoutSerializer(serializers.Serializer):
    """Input payload for POST /api/v1/orders/checkout/"""
    address_id = serializers.IntegerField()
    delivery_slot = serializers.CharField(max_length=100, required=False, allow_blank=True)
    payment_method = serializers.ChoiceField(choices=[("cod", "cod"), ("online", "online")])
    notes = serializers.CharField(max_length=250, required=False, allow_blank=True)


class SiteConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteConfig
        fields = [
            "site_name", "tagline", "banner_message", "contact_phone", "contact_whatsapp",
            "contact_email", "delivery_fee", "free_delivery_above", "min_order_value", "gst_percent",
        ]
