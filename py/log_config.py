# py/log_config.py
import logging
from logging.handlers import RotatingFileHandler
from logging import StreamHandler

# Optional Logflare integration
try:
    from py.logflare_handler import LogflareHandler
    _has_logflare = True
except ImportError:
    _has_logflare = False


# ─── 1) Configure root logger to INFO level (change to DEBUG if needed) ───
root = logging.getLogger()
root.setLevel(logging.INFO)

fmt = logging.Formatter(
    "%(asctime)s [%(levelname)-5s] %(name)s:%(funcName)s:%(lineno)d — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# ─── 2) Console Handler ───
ch = StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(fmt)
root.addHandler(ch)

# ─── 3) Rotating File Handler ───
fh = RotatingFileHandler("discord_bot.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8")
fh.setLevel(logging.INFO)
fh.setFormatter(fmt)
root.addHandler(fh)

# ─── 4) Optional: Logflare Handler ───
try:
    lh = LogflareHandler()
    lh.setLevel(logging.INFO)
    lh.setFormatter(fmt)
    root.addHandler(lh)
except Exception as e:
    root.warning("LogflareHandler init fehlgeschlagen: %s", e)

# ─── 5) Expose a module‐level logger for “app code” ───
logger = logging.getLogger(__name__)