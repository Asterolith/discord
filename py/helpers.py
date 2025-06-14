# py/helpers.py
import os, time
from supabase import create_client
from py.log_config import logger


# ─── Config ─────────────────────────────────────────────────────────────────────
SUPABASE_URL    = os.getenv("SUPABASE_URL")
SB_ANON_KEY     = os.getenv("SUPABASE_ANON_KEY")
SB_SERVICE_KEY  = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


if not all([SUPABASE_URL, SB_ANON_KEY, SB_SERVICE_KEY]):
    logger.error("Missing required Supabase or JWT environment variables")
    raise RuntimeError("Missing Supabase or JWT environment variables")

# ─── Supabase clients ─────────────────────────────────────────────────────────
anon_supabase = create_client(SUPABASE_URL, SB_ANON_KEY)
admin_supabase = create_client(SUPABASE_URL, SB_SERVICE_KEY)

# ─── Formatting constants ─────────────────────────────────────────────────────
NAME_WIDTH = 15
SING_WIDTH = 7
DANCE_WIDTH = 7
RALLY_WIDTH = 7
ROWS_PER_PAGE = 20
HEADER = (
    f"{'Name':<{NAME_WIDTH}} | "
    f"{'Sing[k]':<{SING_WIDTH}}|"
    f"{'Dance[k]':<{DANCE_WIDTH}}| "
    f"{'Rally[Mio]':<{RALLY_WIDTH}}"
)
SEP = '-' * len(HEADER)

# ─── Auth / Admin Check ──────────────────────────────────────────────────────────
def load_admin_ids(path="data/adms.txt"):
    ids = set()
    try:
        with open(path, "r") as f:
            for line in f:
                text = line.strip()
                if not text:
                    continue
                try:
                    ids.add(int(text))
                except ValueError:
                    # Skip lines that aren't valid integers
                    continue
    except FileNotFoundError:
        pass
    return ids

# Now ADMIN_IDS is initialized from that file:
ADMIN_IDS = load_admin_ids()


def is_admin(user) -> bool:
    return getattr(user, 'id', None) in ADMIN_IDS


def is_editor(user_id: int) -> bool:
    """Return True if user is in stats_editors_rights table."""
    try:
        res = anon_supabase.table("stats_editors_rights") \
            .select("discord_id") \
            .eq("discord_id", user_id) \
            .execute()
        return bool(res.data)
    except Exception as e:
        logger.error("RLS check failed for editor rights: %s", e)
        return False

# ─── JWT minting & user client ─────────────────────────────────────────────────
# def mint_discord_user_token(discord_id: int, ttl: int = 3600) -> str:
#     now = int(time.time())
#     payload = {
#         "iat": now,
#         "exp": now + ttl,
#         "sub": str(discord_id),
#         "aud": "authenticated",
#         "role": "authenticated",
#         "discord_id": discord_id
#     }
#     return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


# ─── In-memory caching ─────────────────────────────────────────────────────────
_cache = {"data": None, "timestamp": 0}
CACHE_TTL = 60  # seconds


def load_data(use_cache: bool = True) -> list:
    now = time.time()
    if use_cache and _cache["data"] and now - _cache["timestamp"] < CACHE_TTL:
        return _cache["data"]
    try:
        res = anon_supabase.table("stats").select("*").execute()
        data = res.data or []
    except Exception as e:
        logger.error("Failed to load stats data: %s", e)
        return []
    _cache.update({"data": data, "timestamp": now})
    return data


def invalidate_cache() -> None:
    _cache["timestamp"] = 0


# ─── Data modifications ────────────────────────────────────────────────────────
def update_row(name: str, **kwargs) -> None:
    payload = {k: v for k, v in kwargs.items() if v is not None}
    if not payload:
        return
    try:
        anon_supabase.table("stats").update(payload).eq("name", name).execute()
    except Exception as e:
        logger.error("Failed to update row %s: %s", name, e)

# ─── Formatting helpers ─────────────────────────────────────────────────────────
def format_row(d: dict) -> str:
    name = d.get("name", "")
    sing = d.get("sing", 0) or 0
    dance = d.get("dance", 0) or 0
    rally = d.get("rally", 0) or 0
    return (
        f"{name:<{NAME_WIDTH}} | "
        f"{sing:<{SING_WIDTH}}| "
        f"{dance:<{DANCE_WIDTH}}| "
        f"{rally:<{RALLY_WIDTH}}"
    )

def blank_row() -> str:
    return (
        f"{'':<{NAME_WIDTH}} | "
        f"{'':<{SING_WIDTH}}| "
        f"{'':<{DANCE_WIDTH}}| "
        f"{'':<{RALLY_WIDTH}}"
    )


# ─── Sorting & pagination ──────────────────────────────────────────────────────
def sort_data(data: list, column: str, descending: bool = False) -> list:
    key_fn = lambda row: row.get(column) if row.get(column) is not None else (
        "" if column == "name" else float('-inf')
    )
    return sorted(data, key=key_fn, reverse=descending)


# Users of this module should import: 
#   anon_supabase, admin_supabase, is_admin, is_editor, 
#   user_client_for, load_data, invalidate_cache, update_row,
#   HEADER, SEP, format_row, blank_row, sort_data, ROWS_PER_PAGE