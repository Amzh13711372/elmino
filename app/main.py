import os
import json
import threading
import requests
from flask import Flask, request, redirect, session, render_template, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app = Flask(__name__, template_folder=TEMPLATES_DIR)
app.secret_key = os.environ.get("APP_SECRET", "test-secret-key-change-this")

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

CALLBACK = os.environ.get(
    "ZARINPAL_CALLBACK_URL",
    "https://elmino.onrender.com/zarinpal/callback"
)


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


@app.route("/")
def home():
    user = session.get("user")
    coins = 0
    if user:
        users = load_users()
        coins = users.get(user, {}).get("coins", 0)
    return render_template("home.html", user=user, coins=coins)


@app.route("/landing")
def landing():
    return render_template("landing.html")


@app.route("/intro")
def intro():
    return render_template("intro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        users = load_users()
        user = users.get(username)

        if not user or user.get("password") != password:
            return "Invalid username or password", 401

        session["user"] = username
        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            return "Username and password required", 400

        users = load_users()
        if username in users:
            return "User already exists", 400

        users[username] = {
            "password": password,
            "coins": 0
        }
        save_users(users)
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/forgot-password")
def forgot_password():
    return render_template("forgot_password.html")


@app.route("/profile")
def profile():
    return render_template("profile.html")


@app.route("/waiting")
def waiting():
    return render_template("waiting.html")


@app.route("/game")
def game():
    return render_template("game.html")


@app.route("/result")
def result():
    return render_template("result.html")


@app.route("/results")
def results():
    return render_template("results.html")


@app.route("/wallet")
def wallet():
    return render_template("wallet.html")


@app.route("/payment")
def payment():
    return render_template("payment.html")


@app.route("/contest-intro")
def contest_intro():
    return render_template("contest_intro.html")


@app.route("/contest-payment")
def contest_payment():
    return render_template("contest_payment.html")


@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html")


@app.route("/admin-login")
def admin_login():
    return render_template("admin_login.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/admin-questions")
def admin_questions():
    return render_template("admin_questions.html")


@app.route("/help")
def help_page():
    return render_template("help.html")


@app.route("/rules")
def rules():
    return render_template("rules.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/support")
def support():
    return render_template("support.html")


@app.route("/settings")
def settings():
    return render_template("settings.html")


@app.route("/pay")
def pay():
    if "user" not in session:
        return redirect(url_for("login"))

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

        try:
            res_data = res.json()
        except Exception:
            return f"Zarinpal non-JSON response: {res.text}", 500

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

        return f"Error from Zarinpal: data={data_part}, errors={errors_part}", 400

    except Exception as e:
        return f"Request failed: {e}", 500


@app.route("/zarinpal/callback")
def zarinpal_callback():
    authority = request.args.get("Authority")
    status = request.args.get("Status")

    if not authority:
        return "No authority received.", 400

    payments = load_payments()
    payment_data = payments.get(authority)

    if not payment_data:
        return "Payment record not found.", 404

    if status != "OK":
        return "Payment failed or canceled.", 400

    payload = {
        "merchant_id": MERCHANT,
        "amount": payment_data["amount"],
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

        try:
            res_data = res.json()
        except Exception:
            return f"Verify non-JSON response: {res.text}", 500

        data_part = res_data.get("data") or {}
        errors_part = res_data.get("errors") or {}

        if data_part.get("code") in [100, 101]:
            if payment_data.get("verified"):
                return "This payment was already verified."

            username = payment_data["user"]
            users = load_users()

            if username not in users:
                return "User not found.", 404

            users[username]["coins"] += 100
            save_users(users)

            payments[authority]["verified"] = True
            payments[authority]["ref_id"] = data_part.get("ref_id")
            save_payments(payments)

            return f"Payment successful! 100 coins added to {username}. RefID: {data_part.get('ref_id')}"

        return f"Verify failed: data={data_part}, errors={errors_part}", 400

    except Exception as e:
        return f"Verify request failed: {e}", 500


if __name__ == "__main__":
    ensure_data()
    app.run(host="0.0.0.0", port=5000)
