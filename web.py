# web.py:  tiny Flask health endpoint + starts the bot -- OBSOLETE
import os
import threading
from flask import Flask
from bot import bot

app = Flask(__name__)

# Health check for UptimeRobot or Render
@app.route("/", methods=["GET", "HEAD"])
def health():
    return "OK", 200

if __name__ == "__main__":
    # 1) Spawn your Discord bot in a background thread
    threading.Thread(
        target=lambda: bot.run(os.environ["DIS_TOKEN"]),
        daemon=True
    ).start()

    # 2) Run Flask (only used by Gunicorn in production)
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

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