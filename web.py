# web.py:  tiny Flask health endpoint + starts the bot

import os
import time
import threading

from flask import Flask
from bot import bot
from py.log_config import logger

app = Flask(__name__)


@app.route('/')
def index():
    return "BOT is running!", 200

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


def run_bot_w_backoff():
    token = os.environ.get("DIS_TOKEN")
    if not token:
        logger.error("DIS_TOKEN missing - bot not started")
        return

    # initiate waiting time
    backoff = 5
    max_backoff = 200

    while True:
        try:
            logger.info(f"🤖 Start Bot (reconnect=False), Backoff actual: {backoff}s")
            bot.run(token, reconnect=False)
            #_bot.run() blocks until the bot is ready
            logger.info("⚙️ Bot.run() ended")
            break
        except Exception as e:
            logger.error(f"❌ Bot failed: {e}", exc_info=True)
            logger.info(f"⏳ Retrying in {backoff}s")
            time.sleep(backoff)
            #_exponential backoff
            backoff = min(backoff * 2, max_backoff)
            continue


if __name__ == "__main__":
    # Start the bot in a background thread
    threading.Thread(target=run_bot_w_backoff, daemon=True).start()

    logger.info("🌐 Flask web server starting…")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
