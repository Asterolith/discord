# py/helpers.py
import os, time, jwt
from supabase import create_client, Client

# ─── Config ─────────────────────────────────────────────────────────────────────
SUPABASE_URL          = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY     = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY  = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
JWT_SECRET            = os.getenv("SUPABASE_JWT_SECRET")

if not SUPABASE_URL or not SUPABASE_ANON_KEY or not SUPABASE_SERVICE_KEY:
    print("❌ Missing Supabase environment variables!")
    exit(1)

print("🔑 SUPABASE_URL:", SUPABASE_URL)
print("🔑 ANON_KEY LEN:", len(SUPABASE_ANON_KEY or ""))
print("🔑 SERVICE_KEY LEN:", len(SUPABASE_SERVICE_KEY or ""))

# Formatting widths
NAME_WIDTH   = 15
SING_WIDTH   = 7
DANCE_WIDTH  = 7
RALLY_WIDTH  = 7
ROWS_PER_PAGE = 20

# ─── Supabase Clients ────────────────────────────────────────────────────────────
def user_client_for(discord_id: int) -> Client:
    token = mint_discord_user_token(discord_id)
    print(f"[DEBUG] Minted token for {discord_id}: {token[:20]}...")
    return create_client(SUPABASE_URL, token)

anon_supabase  = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
admin_supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
print("[DEBUG] admin_supabase is using SERVICE_KEY:", SUPABASE_SERVICE_KEY[:10], "...")
print("[DEBUG] anon_supabase is using ANON_KEY:", SUPABASE_ANON_KEY[:10], "...")


# ─── Auth / Admin Check ──────────────────────────────────────────────────────────
# ADMIN_IDS = {762749123770056746}
ADMIN_IDS = {}

def is_admin(user) -> bool:
    return user.id in ADMIN_IDS

def is_editor(user_id: int) -> bool:
    """Check table_editors_rights via anon client."""
    res = anon_supabase.table("stats_editors_rights")\
                    .select("*discord_id")\
                    .eq("discord_id", user_id)\
                    .execute()
    return bool(res.data)

def mint_discord_user_token(discord_id: int, ttl: int = 3600) -> str:
    """Mint a JWT token for Supabase RLS with 'discord_id' claim."""
    now = int(time.time())
    payload = {
        "iat": now,
        "exp": now + ttl,
        "sub": str(discord_id),
        "aud": "authenticated",
        "role": "authenticated",
        "discord_id": discord_id,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

# ─── Data I/O ─────────────────────────────────────────────────────────────────────
_cache = {"data": None, "timestamp": 0}
CACHE_TTL = 60  # seconds

def load_data(use_cache=True):
    now = time.time()
    if use_cache and _cache["data"] and now - _cache["timestamp"] < CACHE_TTL:
        return _cache["data"]

    res = anon_supabase.table("stats").select("*").execute()
    _cache["data"] = res.data or []
    _cache["timestamp"] = now
    return _cache["data"]

def invalidate_cache():
    _cache["timestamp"] = 0

def update_row(name, **kwargs):
    update_data = {k: v for k, v in kwargs.items() if v is not None}
    if update_data:
        anon_supabase.table("stats").update(update_data).eq("name", name).execute()

# ─── Formatting ──────────────────────────────────────────────────────────────────
def format_header():
    return (
        f"{'Name':<{NAME_WIDTH}} | "
        f"{'Sing[k]':<{SING_WIDTH}}|"
        f"{'Dance[k]':<{DANCE_WIDTH}}| "
        f"{'Rally[Mio]':<{RALLY_WIDTH}}"
    )

def format_row(d):
    name  = d.get("name", "")
    sing  = d.get("sing") or 0
    dance = d.get("dance") or 0
    rally = d.get("rally") or 0
    return (
        f"{name:<{NAME_WIDTH}} | "
        f"{sing:<{SING_WIDTH}}| "
        f"{dance:<{DANCE_WIDTH}}| "
        f"{rally:<{RALLY_WIDTH}}"
    )

def blank_row():
    return (
        f"{'':<{NAME_WIDTH}} | "
        f"{'':<{SING_WIDTH}}| "
        f"{'':<{DANCE_WIDTH}}| "
        f"{'':<{RALLY_WIDTH}}"
    )

def sort_data(data, column: str, descending: bool = False):
    def key_fn(row):
        v = row.get(column)
        return v if v is not None else ("" if column == "name" else -999999)
    return sorted(data, key=key_fn, reverse=descending)

# ─── Static Header & Separator ────────────────────────────────────────────────────
HEADER = format_header()
SEP    = "-" * len(HEADER)


# def load_page(sort_by: str = None, sort_desc: bool = False, page: int = 1):
#     """
#     Fetch the full list, optionally sort in Python, then slice out a single page.
#     This avoids unsupported .order() calls in the Supabase client.
#     """
#     all_rows = load_data()          # Pull everything (you can limit columns in real use)
#     if sort_by:
#         all_rows = sort_data(all_rows, sort_by, sort_desc)

#     start = (page - 1) * ROWS_PER_PAGE
#     return all_rows[start : start + ROWS_PER_PAGE]