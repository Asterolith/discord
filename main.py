#_main.py
import os, threading
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask

from py.helpers import (
    supabase, admin_supabase, load_page, load_data,
    update_row, invalidate_cache, is_admin,
    HEADER, SEP, format_row, blank_row
)
from py.paginator import TablePaginator


# — Env & Discord token —
TOKEN = os.getenv("DIS_TOKEN", "").strip()
if not TOKEN:
    raise RuntimeError("DIS_TOKEN missing")
print(f"✅ Discord token length: {len(TOKEN)}")

# — Flask app with health check —
# app = Flask(__name__)
# @app.route("/", methods=["GET", "HEAD"])
# def health():
#     return "OK", 200

# # A tiny WSGI filter that catches HEAD/GET on “/” and responds directly, bypassing Flask entirely.
def health_check(environ, start_response):
    method = environ.get("REQUEST_METHOD", "")
    path   = environ.get("PATH_INFO", "")
    if path == "/" and method in ("GET", "HEAD"):
        status = "200 OK"
        headers = [("Content-Type", "text/plain; charset=utf-8")]
        start_response(status, headers)
        return [b"BOT is alive"]
    return app.wsgi_app(environ, start_response)

# 2) Now import Flask and tell Flask to use our filter first
app = Flask(__name__)
app.wsgi_app = health_check

# 3) Keep a normal route too, for local dev
@app.route("/", methods=["GET","HEAD"])
def home():
    return "BOT is alive", 200


# — Discord bot setup —
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user.name} ({bot.user.id})")

# ————————————————————————————————
# Slash Commands
# — show_table command —
@tree.command(name="show_table", description="Show table with sort & pagination")
@app_commands.describe(
    sort_by="name, sing, dance, or rally",
    sort_desc="false for ascending order",
    page="page number"
)
async def show_table(
    interaction: discord.Interaction,
    sort_by: str = None,
    sort_desc: bool = True,
    page: int = 1
):
     # 1) Defer the response so Discord doesn’t timeout
    await interaction.response.defer(thinking=True)

    # 2) Validate sort_by
    if sort_by and sort_by.lower() not in ['name', 'sing', 'dance', 'rally']:
        return await interaction.followup.send("❌ Invalid sort column")

    # Fetch only the rows needed for this page:
    page_data = load_page(sort_by, sort_desc, page)
    if not page_data:
        return await interaction.followup.send("❌ Page out of range")

    # Format and build block
    lines = [HEADER, SEP]
    for row in page_data:
        lines.append(format_row(row))
        lines.append(blank_row())
    block = f"```css\n{chr(10).join(lines)}\n```"

    # Pass the list itself into the paginator, not just its length:
    view = TablePaginator(load_data(), sort_by, sort_desc, page)

    # 3) Send with followup
    await interaction.followup.send(content=block, view=view)

# — update_table —
@tree.command(name="update_table", description="Update a row in the table")
@app_commands.describe(name="entry name", sing="sing value", dance="dance value", rally="rally value")
async def update_table(
    interaction: discord.Interaction,
    name: str,
    sing: int,
    dance: int,
    rally: float = None
):
    for row in load_data():
        if row["name"].lower() == name.lower():
            update_row(name, sing=sing, dance=dance, rally=rally)
            # Build feedback message dynamically
            feedback = []
            if sing is not None: feedback.append(f"sing={sing}")
            if dance is not None: feedback.append(f"dance={dance}")
            if rally is not None: feedback.append(f"rally={rally}")
            invalidate_cache()
            return await interaction.response.send_message(
                f"✅ Updated `{name}` with {' '.join(feedback)}"
            )
    await interaction.response.send_message(f"❌ No entry found for `{name}`")

# — add_row —
@tree.command(name="add_row", description="Add a new row (admin only)")
async def add_row(
    interaction: discord.Interaction,
    name: str,
    sing: int,
    dance: int,
    rally: float
):
    if not is_admin(interaction.user):
        return await interaction.response.send_message("❌ You are NOT authorized.")

    admin_supabase.table("stats").insert({
        "name": name, "sing": sing, "dance": dance, "rally": rally
    }).execute()
    invalidate_cache()
    await interaction.response.send_message(f"✅ Row for `{name}` added.")

# — delete_row —
@tree.command(name="delete_row", description="Delete a row (admin only)")
async def delete_row(interaction: discord.Interaction, name: str):
    if not is_admin(interaction.user):
        return await interaction.response.send_message("❌ You are not authorized.")

    await interaction.response.defer(thinking=True)

    try:
        res = admin_supabase.table("stats").delete().eq("name", name).execute()
    except Exception as e:
        return await interaction.followup.send(f"❌ Delete failed: {e}")

    if not res.data:
        return await interaction.followup.send(f"❌ No row found for `{name}` to delete.")

    invalidate_cache()
    await interaction.followup.send(f"🗑️ Row for `{name}` deleted.")


# — Run bot in background & WSGI —
def start_bot():
    bot.run(TOKEN)

# Start Discord in a background thread; Flask (Gunicorn) will serve the HTTP side.
threading.Thread(target=start_bot, daemon=True).start()