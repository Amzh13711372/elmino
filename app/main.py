import os, json, hashlib, secrets, threading
from flask import Flask, request, session, render_template, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET", "super-secret-key-123")
DATA_DIR = os.path.expanduser("~/elmino/app/data")
lock = threading.RLock()

def get_data(file):
    path = os.path.join(DATA_DIR, file)
    if not os.path.exists(path): return {"users": [], "transactions": [], "withdrawals": []}
    with open(path, "r", encoding="utf-8") as f: return json.load(f)

def save_data(file, data):
    with lock:
        path = os.path.join(DATA_DIR, file)
        with open(path + ".tmp", "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(path + ".tmp", path)

@app.route("/")
def index(): return "Elmino Online - System Ready"

@app.route("/admin")
def admin():
    data = get_data("withdrawals.json")
    return str(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
