# web.py:  tiny Flask health endpoint + starts the bot -- OBSOLETE
# web.py
import os, threading
from flask import Flask
from bot import bot

# ── Spawn the Discord bot immediately on import ────────────────────────────────
threading.Thread(
    target=lambda: bot.run(os.environ["DIS_TOKEN"]),
    daemon=True
).start()

# ── Flask health‐check app ─────────────────────────────────────────────────────
app = Flask(__name__)

@app.route("/", methods=["GET", "HEAD"])
def health():
    return "OK", 200


# # 1) A tiny WSGI filter that catches HEAD/GET on “/” and responds directly, bypassing Flask entirely.
# def health_check(environ, start_response):
#     method = environ.get("REQUEST_METHOD", "")
#     path   = environ.get("PATH_INFO", "")
#     if path == "/" and method in ("GET", "HEAD"):
#         status = "200 OK"
#         headers = [("Content-Type", "text/plain; charset=utf-8")]
#         start_response(status, headers)
#         return [b"BOT is alive"]
#     return app.wsgi_app(environ, start_response)

# # 2) Now import Flask and tell Flask to use our filter first
# app = Flask(__name__)
# app.wsgi_app = health_check

# # 3) Keep a normal route too, for local dev
# @app.route("/", methods=["GET","HEAD"])
# def home():
#     return "BOT is alive", 200