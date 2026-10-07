import os
import sys
from decimal import Decimal
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.db.models import Count, Sum
from catalog.models import Product, Category
from orders.models import Order, OrderItem


st.set_page_config(
    page_title="MNSEA Kings Dashboard",
    page_icon="🐟",
    layout="wide",
)


@st.cache_data
def get_dashboard_data():
    total_products = Product.objects.count()
    total_categories = Category.objects.filter(is_active=True).count()
    total_orders = Order.objects.count()

    total_revenue = (
        Order.objects.filter(payment_status="paid").aggregate(total=Sum("total"))["total"]
        or Decimal("0")
    )

    status_breakdown = list(
        Order.objects.values("status").annotate(count=Count("id")).order_by("-count")
    )

    recent_orders = list(
        Order.objects.order_by("-placed_at")[:5].values(
            "order_number",
            "status",
            "total",
            "placed_at",
            "full_name",
        )
    )

    top_products = list(
        OrderItem.objects.values("product_name")
        .annotate(
            units_sold=Sum("qty"),
            total_revenue=Sum("line_total"),
        )
        .order_by("-units_sold")[:10]
    )

    featured = Product.objects.filter(is_featured=True).count()
    available = Product.objects.filter(is_available=True).count()

    return {
        "total_products": total_products,
        "total_categories": total_categories,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "status_breakdown": status_breakdown,
        "recent_orders": recent_orders,
        "top_products": top_products,
        "featured": featured,
        "available": available,
    }


data = get_dashboard_data()

st.title("🐟 MNSEA Kings Dashboard")
st.caption("Separate Streamlit app connected to the project database.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Products", data["total_products"])
col2.metric("Categories", data["total_categories"])
col3.metric("Orders", data["total_orders"])
col4.metric("Revenue", f"₹{data['total_revenue']:.2f}")

st.markdown("---")

col5, col6 = st.columns(2)
with col5:
    st.subheader("Inventory snapshot")
    st.metric("Featured items", data["featured"])
    st.metric("Available items", data["available"])

with col6:
    st.subheader("Order status")
    if data["status_breakdown"]:
        status_df = [{"status": item["status"], "orders": item["count"]} for item in data["status_breakdown"]]
        st.dataframe(status_df, use_container_width=True, hide_index=True)
    else:
        st.info("No orders yet.")

st.markdown("---")

left_col, right_col = st.columns(2)

with left_col:
    st.subheader("Recent orders")
    if data["recent_orders"]:
        recent_df = [
            {
                "Order": order["order_number"],
                "Customer": order["full_name"],
                "Status": order["status"],
                "Total": f"₹{order['total']}",
                "Placed": order["placed_at"].strftime("%Y-%m-%d %H:%M"),
            }
            for order in data["recent_orders"]
        ]
        st.dataframe(recent_df, use_container_width=True, hide_index=True)
    else:
        st.info("No orders recorded yet.")

with right_col:
    st.subheader("Top selling products")
    if data["top_products"]:
        top_df = [
            {
                "Product": item["product_name"],
                "Units sold": item["units_sold"],
                "Revenue": f"₹{item['total_revenue']}",
            }
            for item in data["top_products"]
        ]
        st.dataframe(top_df, use_container_width=True, hide_index=True)
    else:
        st.info("No product sales yet.")

st.sidebar.header("MNSEA Kings")
st.sidebar.write("This Streamlit app is separate from the Django website.")
st.sidebar.write("Run with: streamlit run app.py")
