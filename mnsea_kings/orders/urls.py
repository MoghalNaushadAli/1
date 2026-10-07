from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("address/", views.address_book, name="address_book"),
    path("checkout/", views.checkout, name="checkout"),
    path("success/<str:order_number>/", views.order_success, name="order_success"),
    path("my-orders/", views.order_history, name="order_history"),
    path("my-orders/<str:order_number>/", views.order_detail, name="order_detail"),
]
