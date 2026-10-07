# 🦈 MNSEA KINGS CORPORATION — Website + Mobile API + Payments (Phase 1 + 2)

A full working **Django** backend for a seafood, prawns, chicken & mutton delivery
business:
- **Phase 1 (website)** — product catalog, cart, checkout, order tracking, and
  an admin panel your brother can use daily to update prices, stock, and orders.
- **Phase 2 (this update)** — a **REST API** (Django REST Framework + JWT) so
  the same backend can power an Android/iOS app with zero data migration, plus
  **Razorpay payment integration** covering UPI (GPay, PhonePe, Paytm, BHIM —
  any UPI app), debit/credit cards, netbanking and wallets, all through one
  checkout widget/SDK.

Both the website and the future mobile app share the exact same database,
products, prices, and order logic — update a price once in the admin, it's
correct everywhere.

---

## ✨ What's included

- **Product catalog** — 5 categories pre-loaded (Fish 🐟, Prawns 🦐, Chicken 🍗,
  Mutton 🐐, Other Seafood 🦑) with 19 sample products (Rohu, Pomfret, Tiger
  Prawns, Chicken Boneless, Mutton Curry Cut, Crab, etc.) at realistic prices —
  delete/edit/add real ones from the admin.
- **Daily price updates, no code needed** — In the admin, the Products list has
  an **editable Price column** right in the table. Your brother can update
  today's prices for many items in one screen and hit Save. There's also an
  MRP field to show a strike-through discount price.
- **Cart & checkout** — session-based cart, address book (multiple saved
  addresses), delivery slot picker, Cash-on-Delivery or UPI payment method,
  automatic delivery fee logic (flat fee, waived above a configurable order
  value — both editable from admin).
- **Accounts** — customer registration/login, order history, profile page.
- **Order management** — every order gets a unique order number
  (e.g. `MNSK2608270001`), and the admin has a dashboard to see/update order
  status (Placed → Confirmed → Packed → Out for Delivery → Delivered).
- **Site settings from the admin** — delivery fee, free-delivery threshold,
  minimum order value, banner message, contact phone/email/UPI ID — all
  editable without touching code (Admin → Core → Site Configuration).
- **Brand theme** — navy & gold theme matching the shark logo, mobile-first
  responsive layout (Bootstrap 5), category & product cards, order status
  pills.
- **💳 Real payments via Razorpay** — "Pay Online" at checkout opens Razorpay
  Checkout, which natively supports **every UPI app (GPay, PhonePe, Paytm,
  BHIM, etc. via UPI intent/collect/QR), debit & credit cards, netbanking, and
  wallets** — all in one integration, no separate SDK needed per app. Cash on
  Delivery remains available too. Payments are cryptographically verified
  (HMAC signature) before an order is marked paid, plus an optional webhook
  as a safety net.
- **📱 REST API for the mobile app** — JWT-authenticated API exposing the
  exact same products, cart, addresses, checkout and orders the website
  uses — see [API Reference](#-rest-api-reference-for-the-mobile-app) below.

---

## 🗂️ Project structure

```
mnsea_kings/
├── config/          Django project settings & URLs
├── core/            Home page, About/Contact, site-wide settings (SiteConfig), pricing.py (shared totals logic)
├── catalog/         Category & Product models, shop pages, admin price editing
├── cart/            Session-based cart (web/guests) + CartItem model (API/mobile, per-user)
├── orders/          Address book, checkout, order history/tracking, payment fields on Order
├── accounts/        Registration, login, profile
├── payments/        Razorpay integration — order creation, signature verification, webhook, PaymentLog audit trail
├── api/              REST API (DRF + JWT) for the mobile app — serializers, views, urls
├── templates/       All HTML templates (base.html = shared layout/navbar/footer)
├── static/           CSS, logo image
├── media/            Uploaded product photos (created after you upload via admin)
├── .env.example      Copy to `.env` and fill in your Razorpay keys (never commit `.env`)
└── manage.py
```

---

## 🚀 Run it locally (Windows/Mac/Linux)

**1. Create a virtual environment & install dependencies**
```bash
cd mnsea_kings
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
```

**2. Set up the database** (SQLite — zero configuration, a `db.sqlite3` file
is created automatically)
```bash
python manage.py migrate
python manage.py seed_demo_data     # loads 5 categories + 19 sample products
```

**3. Create the owner/admin login**
```bash
python manage.py createsuperuser
```
> A demo admin account is already included for you to try immediately:
> **username:** `admin` **password:** `MnSeaKings@2026`
> ⚠️ Change this password immediately (Admin → change password) before going live.

**4. (Optional but recommended) Set up Razorpay for online payments** — see
the [Razorpay setup section](#-setting-up-razorpay-upi--gpay--phonepe--cards--netbanking)
below. Without this, the site works perfectly fine with Cash on Delivery only.

**5. Run the site**
```bash
python manage.py runserver
```
Open **http://127.0.0.1:8000/** for the website,
**http://127.0.0.1:8000/admin/** for the owner's admin dashboard, and
**http://127.0.0.1:8000/api/v1/** for the mobile app's REST API.

---

## 💰 Daily price updates (for your brother)

1. Go to `/admin/` and log in.
2. Click **Catalog → Products**.
3. Edit the **Price** (and MRP, Stock/Available) column directly in the table
   for as many products as needed.
4. Click **Save** at the bottom — all changes go live instantly on the website.

To add a new product: **Catalog → Products → Add Product**, pick a category,
set unit (per kg / per 500g / per piece etc.), price, and upload a photo.

## 📒 Monthly stock books and daily tabs

The admin has a **Stock Ledger** section for month-by-month stock tracking.

1. Go to **Admin → Stock Ledger → Monthly Stock Books → Add Monthly Stock Book**
   and select the year and month, for example August 2026.
2. Select the month and choose **Generate all daily tabs and active products**.
   This creates one **Stock Day** for every calendar day and a line for every
   active product, grouped by category in the admin and Excel export.
3. Open each Stock Day and enter **Received**, **Sold**, **Returns**, and
   **Wastage** quantities. Opening and Closing are calculated automatically:
   `Closing = Opening + Received + Returns - Sold - Wastage`.
4. Choose **Recalculate carried-forward opening quantities** on the monthly
   book after correcting an earlier day. The previous day's closing quantity,
   including returns, becomes the next day's opening quantity. The final day
   also carries into the next month's first day.
5. Choose **Export selected month as Excel workbook** to download a workbook
   with a Monthly Summary tab plus one tab for every day.
6. When the month is checked, choose **Close selected month**. Closed books
   cannot be edited, preserving the audit trail.

---

## 🧾 Orders

- Orders appear in **Admin → Orders → Orders**. You can filter by status,
  search by order number/phone/pincode, and update status (Confirmed → Packed
  → Out for Delivery → Delivered) — the customer sees the updated status
  next time they check "My Orders".
- Customers can track their own orders at `/orders/my-orders/` after logging in.

---

## ⚙️ Site-wide settings (no code)

**Admin → Core → Site Configuration** lets you change, without any code:
- Delivery fee & free-delivery order threshold
- Minimum order value
- Contact phone/WhatsApp/email, UPI ID
- Top banner message shown on every page

---

## 💳 Setting up Razorpay (UPI / GPay / PhonePe / Cards / Netbanking)

Razorpay is the payment gateway wired in — it's the standard choice for
Indian businesses and one integration covers **every UPI app, all major
cards, netbanking and wallets** automatically:

1. Sign up at **https://dashboard.razorpay.com** (instant approval for Test
   Mode — you can start testing today; full KYC is only needed to accept
   real live payments later).
2. Go to **Settings → API Keys → Generate Test Key**. Copy the **Key Id** and
   **Key Secret**.
3. In the project folder, copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
4. Paste your keys into `.env`:
   ```
   RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxx
   RAZORPAY_KEY_SECRET=your_test_secret_here
   ```
5. Restart the server. The "UPI / Cards / Netbanking (Pay Online)" option
   will now be enabled at checkout (it's automatically hidden/disabled if
   these keys aren't set, so the site always stays usable with Cash on
   Delivery even before you finish this setup).
6. **Test it**: Razorpay Test Mode gives you fake UPI IDs and card numbers
   that simulate success/failure without moving real money — see
   [Razorpay's test card/UPI docs](https://razorpay.com/docs/payments/payments/test-card-details/).
7. **Go live**: once your Razorpay account is KYC-verified, switch
   `RAZORPAY_KEY_ID`/`RAZORPAY_KEY_SECRET` in `.env` to your **Live** keys
   (no code changes needed).

**Optional but recommended — Webhook (safety net):** if a customer pays but
closes the browser/app before the confirmation call finishes, the webhook
catches it anyway. In Razorpay Dashboard → **Settings → Webhooks → Add New
Webhook**:
- URL: `https://yourdomain.com/payments/webhook/`
- Events: `payment.captured`, `payment.failed`
- Set a secret, and put the same value in `.env` as `RAZORPAY_WEBHOOK_SECRET`

Every payment event (order created, verified, failed, webhook received) is
logged in **Admin → Payments → Payment Logs** for easy support/debugging —
handy for "I paid but my order still shows pending" questions.

---

## 📱 REST API Reference (for the mobile app)

Base URL: `http://<your-server>/api/v1/`

All endpoints return JSON. Authenticated endpoints require an
`Authorization: Bearer <access_token>` header (JWT, valid for 7 days; use
the refresh token — valid 90 days — to get a new one without re-login).

| Method | Endpoint | Auth? | Description |
|---|---|---|---|
| POST | `/auth/register/` | No | `{username, password, first_name, email, phone}` → creates account + returns tokens |
| POST | `/auth/login/` | No | `{username, password}` → `{access, refresh}` |
| POST | `/auth/token/refresh/` | No | `{refresh}` → new `{access}` |
| GET | `/auth/me/` | Yes | Current user's profile |
| GET | `/categories/` | No | List active categories |
| GET | `/products/?category=<slug>&q=<search>&sort=price_low\|price_high\|name&featured=true&bestseller=true` | No | List products (paginated, 20/page) |
| GET | `/products/<slug>/` | No | Product detail |
| GET | `/site-config/` | No | Delivery fee, free-delivery threshold, contact info, banner |
| GET | `/cart/` | Yes | Current user's cart + computed `subtotal`, `delivery_fee`, `total` |
| POST | `/cart/` | Yes | `{product_id, qty}` → add/increment item |
| PATCH | `/cart/items/<id>/` | Yes | `{qty}` → set exact quantity |
| DELETE | `/cart/items/<id>/` | Yes | Remove item from cart |
| GET / POST | `/addresses/` | Yes | List / create delivery addresses |
| GET / PUT / DELETE | `/addresses/<id>/` | Yes | Manage a single address |
| POST | `/orders/checkout/` | Yes | `{address_id, delivery_slot, payment_method: "cod"\|"online", notes}` → creates order; for `"online"` also returns `razorpay.{key_id, razorpay_order_id, amount, currency}` for the app's Razorpay SDK |
| POST | `/orders/verify-payment/` | Yes | `{order_number, razorpay_order_id, razorpay_payment_id, razorpay_signature}` → verifies & marks order paid |
| GET | `/orders/` | Yes | Order history for the logged-in user |
| GET | `/orders/<order_number>/` | Yes | Order detail (items, status, payment status) |

**Mobile app payment flow (React Native / Flutter):**
1. App calls `POST /orders/checkout/` with `payment_method: "online"`.
2. Response includes `razorpay.key_id`, `razorpay_order_id`, `amount`.
3. App opens the **Razorpay mobile Checkout SDK** with those values — it
   shows the same UPI apps/cards/netbanking picker as the website.
4. On success, app calls `POST /orders/verify-payment/` with the values the
   SDK returns — this is what actually marks the order as paid (never trust
   the client-side "success" alone).

**Quick test with curl:**
```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register/ -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"Passw0rd!123","first_name":"Test","email":"t@example.com","phone":"9999999999"}'

# Use the returned "access" token for everything else
curl http://localhost:8000/api/v1/products/?category=fish \
  -H "Authorization: Bearer <access_token>"
```

---

## 🖼️ Product photos

Upload real photos for each product from the admin (Catalog → Products →
open a product → Image field). Recommended: square images, ~800×800px,
good lighting, plain background — this alone makes a huge visual difference.

---

## 🧭 What's next (Phase 3)

1. ~~Payment gateway~~ ✅ Done — Razorpay covers UPI/cards/netbanking/wallets.
2. ~~Mobile app backend~~ ✅ Done — REST API + JWT auth ready; next actual
   step is building the React Native / Flutter app UI that calls it.
3. **Deployment** — for going live, this can be deployed to Railway, Render,
   PythonAnywhere, or an Azure/AWS VM. Before deploying: set `DEBUG = False`,
   set a real `SECRET_KEY` via environment variable, set `ALLOWED_HOSTS`,
   set `CORS_ALLOWED_ORIGINS` to your real app/website domains, and serve
   static/media files via whitenoise or a cloud storage bucket (S3/Azure
   Blob) since product photos will need permanent storage.
4. **SMS/WhatsApp order notifications** — hook up an SMS/WhatsApp API so
   customers get an automatic order-confirmation and status-update message
   (works well combined with the Razorpay webhook already in place).
5. **Push notifications** for the mobile app (order status updates) once
   the app exists — Firebase Cloud Messaging is the usual choice.

---

## 🔒 Before going live — production checklist

- [ ] Change the demo admin password
- [ ] Set `DEBUG = False` in `config/settings.py`
- [ ] Set `SECRET_KEY` from an environment variable, not hardcoded
- [ ] Set `ALLOWED_HOSTS` to your real domain
- [ ] Switch to a production database if expecting heavy traffic (Postgres)
- [ ] Switch Razorpay keys in `.env` from Test mode to Live mode (after KYC)
- [ ] Set up the Razorpay webhook (see setup section above) for payment reliability
- [ ] Set `CORS_ALLOWED_ORIGINS` in `.env` to your real app/website domain(s)
- [ ] Set up a proper email backend (for order confirmation emails)
- [ ] Configure a real domain + SSL (HTTPS) — Razorpay Checkout requires HTTPS in production

---

Built with Django 6 + Bootstrap 5. Questions or want the next feature
(payments, mobile app, admin analytics dashboard) — just ask! 🦈
