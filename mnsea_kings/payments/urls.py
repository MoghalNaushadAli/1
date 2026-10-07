from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("pay/<str:order_number>/", views.initiate_payment, name="initiate_payment"),
    path("verify/<str:order_number>/", views.verify_payment, name="verify_payment"),
    path("webhook/", views.razorpay_webhook, name="webhook"),
]
