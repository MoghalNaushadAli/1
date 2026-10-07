from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

app_name = "api"

urlpatterns = [
    # --- Auth ---
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="login"),          # {username, password} -> {access, refresh}
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", views.MeView.as_view(), name="me"),

    # --- Catalog ---
    path("categories/", views.CategoryListView.as_view(), name="category_list"),
    path("products/", views.ProductListView.as_view(), name="product_list"),
    path("products/<slug:slug>/", views.ProductDetailView.as_view(), name="product_detail"),

    # --- Site config ---
    path("site-config/", views.SiteConfigView.as_view(), name="site_config"),

    # --- Cart (authenticated) ---
    path("cart/", views.CartView.as_view(), name="cart"),
    path("cart/items/<int:pk>/", views.CartItemDetailView.as_view(), name="cart_item_detail"),

    # --- Addresses (authenticated) ---
    path("addresses/", views.AddressListCreateView.as_view(), name="address_list_create"),
    path("addresses/<int:pk>/", views.AddressDetailView.as_view(), name="address_detail"),

    # --- Checkout & payment (authenticated) ---
    path("orders/checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("orders/verify-payment/", views.VerifyPaymentView.as_view(), name="verify_payment"),

    # --- Orders (authenticated) ---
    path("orders/", views.OrderListView.as_view(), name="order_list"),
    path("orders/<str:order_number>/", views.OrderDetailView.as_view(), name="order_detail"),
]
