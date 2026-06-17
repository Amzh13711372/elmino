from flask import Flask, request, redirect, session, render_template_string
import os
import json
import threading
import requests

app = Flask(__name__)
app.secret_key = "test-secret-key-change-this"

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PAYMENTS_FILE = os.path.join(DATA_DIR, "payments.json")
LOCK = threading.RLock()

SANDBOX = True

if SANDBOX:
    MERCHANT = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    ZP_API_REQUEST = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
    ZP_API_VERIFY = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
    ZP_API_STARTPAY = "https://sandbox.zarinpal.com/pg/StartPay/"
else:
    MERCHANT = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    ZP_API_REQUEST = "https://api.zarinpal.com/pg/v4/payment/request.json"
    ZP_API_VERIFY = "https://api.zarinpal.com/pg/v4/payment/verify.json"
    ZP_API_STARTPAY = "https://www.zarinpal.com/pg/StartPay/"

CALLBACK = "https://victor-mall-entertaining-characterization.trycloudflare.com/zarinpal/callback"


def ensure_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    if not os.path.exists(PAYMENTS_FILE):
        with open(PAYMENTS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)


def load_json(path):
    ensure_data()
    with LOCK:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


def save_json(path, data):
    ensure_data()
    with LOCK:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def load_users():
    return load_json(USERS_FILE)


def save_users(data):
    save_json(USERS_FILE, data)


def load_payments():
    return load_json(PAYMENTS_FILE)


def save_payments(data):
    save_json(PAYMENTS_FILE, data)


HOME_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Home</title>
</head>
<body>
  <h2>فروشگاه سکه</h2>

  {% if user %}
    <p>وارد سیستم شده‌اید: <b>{{ user }}</b></p>
    <p>سکه‌ها: <b>{{ coins }}</b></p>
    <p><a href="/pay">خرید 100 سکه</a></p>
    <p><a href="/logout">خروج</a></p>
  {% else %}
    <p><a href="/login">ورود</a></p>
    <p><a href="/register">ثبت نام</a></p>
  {% endif %}
</body>
</html>
"""

REGISTER_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Register</title>
</head>
<body>
  <h2>ثبت نام</h2>
  <form method="post">
    <input name="username" placeholder="username" required><br><br>
    <input name="password" placeholder="password" type="password" required><br><br>
    <button type="submit">Register</button>
  </form>
  <p><a href="/">Home</a></p>
</body>
</html>
"""

LOGIN_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Login</title>
</head>
<body>
  <h2>ورود</h2>
  <form method="post">
    <input name="username" placeholder="username" required><br><br>
    <input name="password" placeholder="password" type="password" required><br><br>
    <button type="submit">Login</button>
  </form>
  <p><a href="/">Home</a></p>
</body>
</html>
"""


@app.route("/")
def home():
    user = session.get("user")
    coins = 0
    if user:
        users = load_users()
        coins = users.get(user, {}).get("coins", 0)
    return render_template_string(HOME_HTML, user=user, coins=coins)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            return "Username and password required"

        users = load_users()
        if username in users:
            return "User already exists"

        users[username] = {
            "password": password,
            "coins": 0
        }
        save_users(users)
        return redirect("/login")

    return render_template_string(REGISTER_HTML)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        users = load_users()
        user = users.get(username)

        if not user or user.get("password") != password:
            return "Invalid username or password"

        session["user"] = username
        return redirect("/")

    return render_template_string(LOGIN_HTML)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/pay")
def pay():
    if "user" not in session:
        return redirect("/login")

    username = session["user"]
    amount = 10000
    description = f"Purchase for {username}"

    payload = {
        "merchant_id": MERCHANT,
        "amount": amount,
        "description": description,
        "callback_url": CALLBACK,
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    try:
        res = requests.post(
            ZP_API_REQUEST,
            data=json.dumps(payload),
            headers=headers,
            timeout=20
        )

        print("========== ZARINPAL REQUEST ==========")
        print("URL:", ZP_API_REQUEST)
        print("PAYLOAD:", payload)
        print("STATUS:", res.status_code)
        print("TEXT:", res.text)
        print("======================================")

        try:
            res_data = res.json()
        except Exception:
            return f"Zarinpal non-JSON response: {res.text}"

        data_part = res_data.get("data") or {}
        errors_part = res_data.get("errors") or {}

        if data_part.get("code") == 100 and data_part.get("authority"):
            authority = str(data_part["authority"])

            payments = load_payments()
            payments[authority] = {
                "user": username,
                "amount": amount,
                "verified": False
            }
            save_payments(payments)

            return redirect(ZP_API_STARTPAY + authority)

        return f"Error from Zarinpal: data={data_part}, errors={errors_part}"

    except Exception as e:
        return f"Request failed: {e}"


@app.route("/zarinpal/callback")
def zarinpal_callback():
    authority = request.args.get("Authority")
    status = request.args.get("Status")

    print("========== CALLBACK ==========")
    print("Authority:", authority)
    print("Status:", status)
    print("==============================")

    if not authority:
        return "No authority received."

    payments = load_payments()
    payment = payments.get(authority)

    if not payment:
        return "Payment record not found."

    if status != "OK":
        return "Payment failed or canceled."

    payload = {
        "merchant_id": MERCHANT,
        "amount": payment["amount"],
        "authority": authority,
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    try:
        res = requests.post(
            ZP_API_VERIFY,
            data=json.dumps(payload),
            headers=headers,
            timeout=20
        )

        print("========== ZARINPAL VERIFY ==========")
        print("URL:", ZP_API_VERIFY)
        print("PAYLOAD:", payload)
        print("STATUS:", res.status_code)
        print("TEXT:", res.text)
        print("=====================================")

        try:
            res_data = res.json()
        except Exception:
            return f"Verify non-JSON response: {res.text}"

        data_part = res_data.get("data") or {}
        errors_part = res_data.get("errors") or {}

        if data_part.get("code") in [100, 101]:
            if payment.get("verified"):
                return "This payment was already verified."

            username = payment["user"]
            users = load_users()

            if username not in users:
                return "User not found."

            users[username]["coins"] += 100
            save_users(users)

            payments[authority]["verified"] = True
            payments[authority]["ref_id"] = data_part.get("ref_id")
            save_payments(payments)

            return f"Payment successful! 100 coins added to {username}. RefID: {data_part.get('ref_id')}"

        return f"Verify failed: data={data_part}, errors={errors_part}"

    except Exception as e:
        return f"Verify request failed: {e}"


if __name__ == "__main__":
    ensure_data()
    app.run(host="0.0.0.0", port=5000)
