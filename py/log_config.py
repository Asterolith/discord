# py/log_config.py
import logging
from logging.handlers import RotatingFileHandler
from postgrest.exceptions import APIError

# —————————————————————————
# Configure the root logger (you can adjust level here)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-4s] %(name)s:%(lineno)d — %(message)s",
    datefmt="%Y.%m.%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# Rotate on disk as well (optional on Render)
handler = RotatingFileHandler(
    filename="app.log", maxBytes=10_000_000, backupCount=3, encoding="utf-8"
)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)-4s] %(name)s:%(lineno)d — %(message)s",
    datefmt="%Y.%m.%d %H:%M:%S"
))
logger.addHandler(handler)


def safe_select(client, table: str, *columns, **options):
    """
    Fetch `columns` from `table`, catch & log any Supabase/APIError,
    then re-raise for the caller to handle gracefully.
    """
    try:
        resp = client.table(table).select(*columns, **options).execute()
        return resp.data or []
    except APIError as err:
        # err.args[0] is that JSON dict with message/code/hint
        logger.error("Supabase SELECT on %s failed: %s", table, err.args[0])
        raise


def safe_update(client, table: str, payload: dict, match: dict):
    try:
        resp = client.table(table).update(payload).match(match).execute()
        return resp.data or []
    except APIError as err:
        logger.error("Supabase UPDATE on %s failed: %s", table, err.args[0])
        raise


def safe_insert(client, table: str, payload: dict):
    try:
        resp = client.table(table).insert(payload).execute()
        return resp.data or []
    except APIError as err:
        logger.error("Supabase INSERT on %s failed: %s", table, err.args[0])
        raise


def safe_delete(client, table: str, match: dict):
    try:
        resp = client.table(table).delete().match(match).execute()
        return resp.data or []
    except APIError as err:
        logger.error("Supabase DELETE on %s failed: %s", table, err.args[0])
        raise