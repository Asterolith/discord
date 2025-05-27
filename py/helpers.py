# Helper Functions
import os
from supabase import create_client, Client


# Constants
NAME_WIDTH = 15
SING_WIDTH = 7
DANCE_WIDTH = 7
RALLY_WIDTH = 7
ROWS_PER_PAGE = 20


# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Missing Supabase environment variables!")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# Data I/O
def load_data():
    res = supabase.table("stats").select("*").execute()
    return res.data or []


def load_page(sort_by: str = None, sort_desc: bool = False, page: int = 1):
    '''Fetch only rows that need from Suppabase DB, already sorted & paged.'''
    start = (page - 1) * ROWS_PER_PAGE
    end = start + ROWS_PER_PAGE - 1
    query = supabase.table("stats").select("*")

    if sort_by:
        #_Superbase ordering expected (ascending: bool)
        query = query.order(sort_by, {"ascending": not sort_desc})

    return query.range(start, end).execute().data or []


def update_row(name, **kwargs):
    update_data = {k: v for k, v in kwargs.items() if v is not None}
    if update_data:
        supabase.table("stats").update(update_data).eq("name", name).execute()


# Formatting
def format_header():
    return (
        f"{'Name':<{NAME_WIDTH}} | "
        f"{'Sing[k]':<{SING_WIDTH}}|"
        f"{'Dance[k]':<{DANCE_WIDTH}}| "
        f"{'Rally[Mio]':<{RALLY_WIDTH}}"
    )


def format_row(d):
    name = d.get('name','')
    sing = d.get('sing') or 0
    dance = d.get('dance') or 0
    rally = d.get('rally') or 0
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


def sort_data(data, column: str, descending: bool=False):
    def key_fn(row):
        v = row.get(column)
        return v if v is not None else ("" if column=='name' else -999999)
    return sorted(data, key=key_fn, reverse=descending)


# Precompute header and separator once
HEADER = format_header()
SEP    = "-" * len(HEADER)