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
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# ─── 2) Console Handler ───
console_handler = StreamHandler()
console_handler.setLevel(logging.INFO)
console_fmt = logging.Formatter(
    "%(asctime)s [%(levelname)-5s] %(name)s:%(funcName)s:%(lineno)d — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
console_handler.setFormatter(console_fmt)
root_logger.addHandler(console_handler)

# ─── 3) Rotating File Handler ───
file_handler = RotatingFileHandler(
    filename="discord_bot.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8"
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(console_fmt)
root_logger.addHandler(file_handler)

# ─── 4) Optional: Logflare Handler ───
# Wrap in try/except so startup won’t fail if Logflare credentials are missing.
if _has_logflare:
    try:
        lf_handler = LogflareHandler()
        lf_handler.setLevel(logging.INFO)
        root_logger.addHandler(lf_handler)
    except Exception as exc:
        root_logger.warning("Failed to initialize Logflare handler: %s", exc)
# try:
#     logflare_handler = LogflareHandler()
#     logflare_handler.setLevel(logging.INFO)
#     # If you prefer a tighter format for Logflare, change this formatter:
#     logflare_fmt = logging.Formatter("%(asctime)s [%(levelname)-5s] %(name)s: %(message)s")
#     logflare_handler.setFormatter(logflare_fmt)
#     root_logger.addHandler(logflare_handler)
# except Exception as e:
#     root_logger.warning("Could not initialize LogflareHandler: %s", e)

# ─── 5) Expose a module‐level logger for “app code” ───
logger = logging.getLogger(__name__)

