import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
if not DATA_DIR.exists():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

USERS_FILE = DATA_DIR / "users.json"
STATE_FILE = DATA_DIR / "state.json"
RESULTS_FILE = DATA_DIR / "results.json"

REQUIRED_PLAYERS = 3
WAIT_TIMEOUT_MINUTES = 10

FIRST_SHARE_PERCENT = 45
SECOND_SHARE_PERCENT = 35
THIRD_SHARE_PERCENT = 15
ADMIN_SHARE_PERCENT = 5

ALLOWED_ENTRY_FEES = [1000, 2000, 5000]

app = FastAPI(title="Elmino Prize Pool")

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def ensure_files():
    if not USERS_FILE.exists():
        USERS_FILE.write_text("{}", encoding="utf-8")

    if not STATE_FILE.exists():
        STATE_FILE.write_text(json.dumps({
            "message": "هنوز مسابقه‌ای شروع نشده است.",
            "last_game_at": None,
            "admin_earnings": 0
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    if not RESULTS_FILE.exists():
        RESULTS_FILE.write_text("[]", encoding="utf-8")


ensure_files()


def load_json(path, default):
    try:
        if not path.exists():
            return default
        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            return default
        data = json.loads(raw)
        return data
    except Exception:
        return default


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_users():
    data = load_json(USERS_FILE, {})
    if isinstance(data, dict):
        return data
    return {}


def save_users(users):
    save_json(USERS_FILE, users)


def load_state():
    data = load_json(STATE_FILE, {})
    if isinstance(data, dict):
        return data
    return {
        "message": "هنوز مسابقه‌ای شروع نشده است.",
        "last_game_at": None,
        "admin_earnings": 0
    }


def save_state(state):
    save_json(STATE_FILE, state)


def load_results():
    data = load_json(RESULTS_FILE, [])
    if isinstance(data, list):
        return data
    return []


def save_results(results):
    save_json(RESULTS_FILE, results)


def now_iso():
    return datetime.utcnow().isoformat()


def get_current_user(request: Request):
    username = request.cookies.get("username")
    if not username:
        return None, None
    users = load_users()
    user = users.get(username)
    return username, user


def create_user(username, password, national_id):
    return {
        "username": username,
        "password": password,
        "national_id": national_id,
        "accepted_rules": False,
        "wallet_balance": 0,
        "deposit_balance": 0,
        "profit_balance": 0,
        "withdrawn_profit": 0,
        "current_escrow": 0,
        "entry_paid": 0,
        "paid": False,
        "joined_waiting_at": None,
        "is_blocked": False,
        "warning_count": 0,
        "created_at": now_iso()
    }


def eligible_paid_players(users):
    players = []
    for username, user in users.items():
        if (
            not user.get("is_blocked", False)
            and user.get("paid") is True
            and user.get("entry_paid", 0) > 0
            and user.get("current_escrow", 0) > 0
        ):
            players.append({
                "username": username,
                "entry_paid": user.get("entry_paid", 0),
                "current_escrow": user.get("current_escrow", 0),
                "joined_waiting_at": user.get("joined_waiting_at")
            })
    return players


def calc_rewards(pool_amount):
    first = int(pool_amount * FIRST_SHARE_PERCENT / 100)
    second = int(pool_amount * SECOND_SHARE_PERCENT / 100)
    third = int(pool_amount * THIRD_SHARE_PERCENT / 100)
    admin = pool_amount - first - second - third
    return first, second, third, admin


def waiting_expired(user):
    joined_at = user.get("joined_waiting_at")
    if not joined_at:
        return False
    try:
        joined_dt = datetime.fromisoformat(joined_at)
        return datetime.utcnow() >= joined_dt + timedelta(minutes=WAIT_TIMEOUT_MINUTES)
    except Exception:
        return False


def can_cancel_waiting(user, users):
    if not user.get("paid"):
        return False

    paid_players = eligible_paid_players(users)
    if len(paid_players) >= REQUIRED_PLAYERS:
        return False

    return waiting_expired(user)


def reset_player_after_game(user):
    user["current_escrow"] = 0
    user["entry_paid"] = 0
    user["paid"] = False
    user["joined_waiting_at"] = None


def run_game_if_ready():
    users = load_users()
    state = load_state()
    results = load_results()

    paid_players = eligible_paid_players(users)
    if len(paid_players) != REQUIRED_PLAYERS:
        return False

    same_fee = len(set(p["entry_paid"] for p in paid_players)) == 1
    if not same_fee:
        state["message"] = "بازیکنان با مبالغ متفاوت وارد شده‌اند. این دور قابل اجرا نیست."
        save_state(state)
        return False

    entry_fee = paid_players[0]["entry_paid"]
    pool = sum(p["current_escrow"] for p in paid_players)

    shuffled = paid_players[:]
    random.shuffle(shuffled)

    first_user = shuffled[0]["username"]
    second_user = shuffled[1]["username"]
    third_user = shuffled[2]["username"]

    first_reward, second_reward, third_reward, admin_reward = calc_rewards(pool)

    ranking = [
        (first_user, 1, first_reward),
        (second_user, 2, second_reward),
        (third_user, 3, third_reward),
    ]

    for username, rank, reward in ranking:
        user = users[username]
        paid_amount = user.get("entry_paid", 0)
        profit = reward - paid_amount

        user["wallet_balance"] = user.get("wallet_balance", 0) + reward
        user["deposit_balance"] = user.get("deposit_balance", 0) + paid_amount
        user["profit_balance"] = user.get("profit_balance", 0) + profit
        reset_player_after_game(user)

    state["admin_earnings"] = state.get("admin_earnings", 0) + admin_reward
    state["last_game_at"] = now_iso()
    state["message"] = f"مسابقه با مبلغ ورودی {entry_fee} تومان اجرا شد."

    game_result = {
        "played_at": now_iso(),
        "entry_fee": entry_fee,
        "pool": pool,
        "admin_reward": admin_reward,
        "players": [
            {"username": first_user, "rank": 1, "reward": first_reward},
            {"username": second_user, "rank": 2, "reward": second_reward},
            {"username": third_user, "rank": 3, "reward": third_reward},
        ]
    }

    results.insert(0, game_result)

    save_users(users)
    save_state(state)
    save_results(results)
    return True


@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/rules", response_class=HTMLResponse)
def rules_page(request: Request):
    username, user = get_current_user(request)
    return templates.TemplateResponse("rules.html", {
        "request": request,
        "username": username,
        "user": user
    })


@app.post("/rules/accept")
def accept_rules(request: Request, accept_rules: str = Form(...)):
    username, user = get_current_user(request)
    if not username or not user:
        return RedirectResponse("/login", status_code=303)

    if accept_rules != "yes":
        return RedirectResponse("/rules", status_code=303)

    users = load_users()
    users[username]["accepted_rules"] = True
    save_users(users)
    return RedirectResponse("/home", status_code=303)


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@app.post("/register", response_class=HTMLResponse)
def register_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    national_id: str = Form(...)
):
    users = load_users()

    username = username.strip()
    national_id = national_id.strip()

    if not username or not password or not national_id:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "همه فیلدها الزامی هستند."
        })

    if username in users:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "این نام کاربری قبلاً ثبت شده است."
        })

    for _, u in users.items():
        if u.get("national_id") == national_id:
            return templates.TemplateResponse("register.html", {
                "request": request,
                "error": "این کد ملی قبلاً ثبت شده است."
            })

    users[username] = create_user(username, password, national_id)
    save_users(users)

    response = RedirectResponse("/rules", status_code=303)
    response.set_cookie("username", username, httponly=True, samesite="lax")
    return response


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login", response_class=HTMLResponse)
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    users = load_users()
    user = users.get(username.strip())

    if not user or user.get("password") != password:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "نام کاربری یا رمز عبور نادرست است."
        })

    if user.get("is_blocked"):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "حساب شما مسدود شده است. با پشتیبانی تماس بگیرید."
        })

    if not user.get("accepted_rules", False):
        response = RedirectResponse("/rules", status_code=303)
        response.set_cookie("username", username.strip(), httponly=True, samesite="lax")
        return response

    response = RedirectResponse("/home", status_code=303)
    response.set_cookie("username", username.strip(), httponly=True, samesite="lax")
    return response


@app.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {
        "request": request,
        "message": None,
        "error": None
    })


@app.post("/forgot-password", response_class=HTMLResponse)
def forgot_password_post(
    request: Request,
    username: str = Form(...),
    national_id: str = Form(...)
):
    users = load_users()
    user = users.get(username.strip())

    if not user or user.get("national_id") != national_id.strip():
        return templates.TemplateResponse("forgot_password.html", {
            "request": request,
            "message": None,
            "error": "اطلاعات وارد شده صحیح نیست."
        })

    return templates.TemplateResponse("forgot_password.html", {
        "request": request,
        "message": f"رمز عبور شما: {user.get('password')}",
        "error": None
    })


@app.get("/logout")
def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("username")
    return response


@app.get("/home", response_class=HTMLResponse)
def home(request: Request):
    username, user = get_current_user(request)
    if not username or not user:
        return RedirectResponse("/login", status_code=303)

    users = load_users()
    can_cancel = can_cancel_waiting(user, users)

    return templates.TemplateResponse("home.html", {
        "request": request,
        "username": username,
        "user": user,
        "can_cancel": can_cancel,
        "allowed_entry_fees": ALLOWED_ENTRY_FEES
    })


@app.get("/wallet", response_class=HTMLResponse)
def wallet_page(request: Request):
    username, user = get_current_user(request)
    if not username or not user:
        return RedirectResponse("/login", status_code=303)

    results = load_results()
    my_results = []

    for result in results:
        for p in result.get("players", []):
            if p.get("username") == username:
                my_results.append({
                    "played_at": result.get("played_at"),
                    "entry_fee": result.get("entry_fee"),
                    "pool": result.get("pool"),
                    "rank": p.get("rank"),
                    "reward": p.get("reward")
                })

    return templates.TemplateResponse("wallet.html", {
        "request": request,
        "username": username,
        "user": user,
        "my_results": my_results[:10]
    })


@app.post("/wallet/charge")
def wallet_charge(request: Request, amount: int = Form(...)):
    username, user = get_current_user(request)
    if not username or not user:
        return RedirectResponse("/login", status_code=303)

    if amount <= 0:
        return RedirectResponse("/wallet", status_code=303)

    users = load_users()
    users[username]["wallet_balance"] = users[username].get("wallet_balance", 0) + amount
    save_users(users)

    return RedirectResponse("/wallet", status_code=303)


@app.get("/payment", response_class=HTMLResponse)
def payment_page(request: Request):
    username, user = get_current_user(request)
    if not username or not user:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse("payment.html", {
        "request": request,
        "username": username,
        "user": user,
        "allowed_entry_fees": ALLOWED_ENTRY_FEES,
        "error": None
    })


@app.post("/payment", response_class=HTMLResponse)
def payment_post(request: Request, entry_fee: int = Form(...)):
    username, user = get_current_user(request)
    if not username or not user:
        return RedirectResponse("/login", status_code=303)

    if user.get("paid") and user.get("current_escrow", 0) > 0:
        return RedirectResponse("/waiting", status_code=303)

    if entry_fee not in ALLOWED_ENTRY_FEES:
        return templates.TemplateResponse("payment.html", {
            "request": request,
            "username": username,
            "user": user,
            "allowed_entry_fees": ALLOWED_ENTRY_FEES,
            "error": "مبلغ انتخابی معتبر نیست."
        })

    if not user.get("accepted_rules", False):
        return RedirectResponse("/rules", status_code=303)

    if user.get("wallet_balance", 0) < entry_fee:
        return templates.TemplateResponse("payment.html", {
            "request": request,
            "username": username,
            "user": user,
            "allowed_entry_fees": ALLOWED_ENTRY_FEES,
            "error": "موجودی کیف پول کافی نیست. ابتدا کیف پول را شارژ کنید."
        })

    users = load_users()
    users[username]["wallet_balance"] = users[username].get("wallet_balance", 0) - entry_fee
    users[username]["current_escrow"] = entry_fee
    users[username]["entry_paid"] = entry_fee
    users[username]["paid"] = True
    users[username]["joined_waiting_at"] = now_iso()
    save_users(users)

    return RedirectResponse("/waiting", status_code=303)


@app.get("/waiting", response_class=HTMLResponse)
def waiting(request: Request):
    username, user = get_current_user(request)
    if not username or not user:
        return RedirectResponse("/login", status_code=303)

    users = load_users()
    state = load_state()
    paid_players = eligible_paid_players(users)
    paid_count = len(paid_players)

    if paid_count == REQUIRED_PLAYERS:
        return RedirectResponse("/game", status_code=303)

    user = users.get(username)
    can_cancel = can_cancel_waiting(user, users)

    return templates.TemplateResponse("waiting.html", {
        "request": request,
        "username": username,
        "user": user,
        "state": state,
        "paid_count": paid_count,
        "required_players": REQUIRED_PLAYERS,
        "players": paid_players,
        "can_cancel": can_cancel,
        "wait_timeout_minutes": WAIT_TIMEOUT_MINUTES
    })


@app.post("/waiting/cancel")
def waiting_cancel(request: Request):
    username, user = get_current_user(request)
    if not username or not user:
        return RedirectResponse("/login", status_code=303)

    users = load_users()
    user = users.get(username)

    if not can_cancel_waiting(user, users):
        return RedirectResponse("/waiting", status_code=303)

    refund = user.get("current_escrow", 0)
    if refund > 0:
        user["wallet_balance"] = user.get("wallet_balance", 0) + refund

    user["current_escrow"] = 0
    user["entry_paid"] = 0
    user["paid"] = False
    user["joined_waiting_at"] = None

    save_users(users)
    return RedirectResponse("/wallet", status_code=303)


@app.get("/game", response_class=HTMLResponse)
def game(request: Request):
    username, user = get_current_user(request)
    if not username or not user:
        return RedirectResponse("/login", status_code=303)

    users = load_users()
    state = load_state()
    paid_players = eligible_paid_players(users)
    paid_count = len(paid_players)

    if paid_count < REQUIRED_PLAYERS:
        return RedirectResponse("/waiting", status_code=303)

    same_fee = len(set(p["entry_paid"] for p in paid_players)) == 1

    return templates.TemplateResponse("game.html", {
        "request": request,
        "username": username,
        "user": user,
        "state": state,
        "paid_count": paid_count,
        "required_players": REQUIRED_PLAYERS,
        "players": paid_players,
        "same_fee": same_fee
    })


@app.post("/game/start")
def game_start(request: Request):
    username, user = get_current_user(request)
    if not username or not user:
        return RedirectResponse("/login", status_code=303)

    ok = run_game_if_ready()
    if not ok:
        return RedirectResponse("/waiting", status_code=303)

    return RedirectResponse("/results", status_code=303)


@app.get("/results", response_class=HTMLResponse)
def results_page(request: Request):
    username, user = get_current_user(request)
    if not username or not user:
        return RedirectResponse("/login", status_code=303)

    results = load_results()
    latest_result = results[0] if results else None

    my_result = None
    if latest_result:
        for p in latest_result.get("players", []):
            if p.get("username") == username:
                my_result = p
                break

    return templates.TemplateResponse("results.html", {
        "request": request,
        "username": username,
        "user": user,
        "latest_result": latest_result,
        "my_result": my_result
    })
