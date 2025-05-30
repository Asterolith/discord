#_main.py
import os, threading
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask
from datetime import datetime

from py.helpers import (
    user_client_for, admin_supabase,
    is_admin,
    ROWS_PER_PAGE, HEADER, SEP,
    format_row, blank_row
)
from py.paginator import TablePaginator

# —————————————————————————————
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

# 1) A tiny WSGI filter that catches HEAD/GET on “/” and responds directly, bypassing Flask entirely.
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

# —————————————————————————————
# — Discord bot setup —
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user.name} ({bot.user.id})")

# ————————————————————————————————
# — Table stats —
# /show_table: pagination & sort for stats
@tree.command(name="show_table", description="Show table with sort & pagination (editor)")
@app_commands.describe(
    sort_by='name | sing | dance | rally',
    sort_desc='Descending order? (default True)',
    page='Page number (default 1)'
)
async def show_table(interaction: discord.Interaction,
                     sort_by: str = None,
                     sort_desc: bool = False,
                     page: int = 1):
    # Defer the response so Discord doesn’t timeout
    await interaction.response.defer(thinking=True)

    # Validate sort_by
    if sort_by and sort_by.lower() not in ('name', 'sing', 'dance', 'rally'):
        return await interaction.followup.send('❌ Invalid sort column')

    # User-scoped client for RLS
    client = user_client_for(interaction.user.id)
    query = client.table('stats').select('*')
    if sort_by:
        query = query.order(sort_by.lower(), ascending=not sort_desc)

    # Pagination
    start = (page - 1) * ROWS_PER_PAGE
    end = start + ROWS_PER_PAGE - 1
    page_data = query.range(start, end).execute().data or []
    if not page_data:
        return await interaction.followup.send('❌ Page out of range')

    # Build text block
    lines = [HEADER, SEP]
    for row in page_data:
        lines.append(format_row(row))
        lines.append(blank_row())
    block = f"```css\n{chr(10).join(lines)}\n```"

    # get total count for pagination buttons
    # you can either keep a cached `load_data` count or do a lightweight
    # count(*) query here, but for simplicity we can fetch all IDs once:
    count = client.table('stats').select('name', {'count': 'exact'}).execute().count
    view = TablePaginator(count, sort_by, sort_desc, page)
    await interaction.followup.send(content=block, view=view)


# — update_table —
@tree.command(name="update_table", description="Update a stats row (editor)")
@app_commands.describe(name='Entry name', sing='New sing value', dance='New dance value', rally='New rally value')
async def update_table(interaction: discord.Interaction,
                       name: str,
                       sing: int,
                       dance: int,
                       rally: float = None):
    await interaction.response.defer(thinking=True)

    client = user_client_for(interaction.user.id)
    # Build update payload, dropping None
    payload = {k: v for k, v in {"sing": sing, "dance": dance, "rally": rally}.items() if v is not None}

    # update the row
    try:
        res = client.table("stats").update(payload).eq("name", name).execute()
    except Exception as e:
        return await interaction.followup.send(f"❌ Update failed: {e}")
    
    # if nothing changed, row didn't exist
    if not(res.data or len(res.data) > 0):
        return await interaction.followup.send(f"❌ No entry found for `{name}`")

    feedback = " ".join(f"{k}={v}" for k, v in payload.items())
    await interaction.followup.send(f"✅ Updated `{name}` with {feedback}")


# — add_row —
@tree.command(name="add_row", description="Add a new row (admin)")
async def add_row(interaction: discord.Interaction,
                  name: str,
                  sing: int,
                  dance: int,
                  rally: float):
    if not is_admin(interaction.user):
        return await interaction.response.send_message("❌NOT authorized.")
    await interaction.response.defer(thinking=True)

    try:
        res = admin_supabase.table("stats")\
                            .insert({"name": name, "sing": sing, "dance": dance, "rally": rally})\
                            .execute()
    except Exception as e:
        return await interaction.followup.send(f"❌ Insert failed: {e}")

    if not (res.data and len(res.data) > 0):
        return await interaction.followup.send("❌ Insert returned no data!")

    await interaction.followup.send(f"✅ Row for `{name}` added.")


# — delete_row —
@tree.command(name="delete_row", description="Delete a row (admin)")
async def delete_row(interaction: discord.Interaction, name: str):
    if not is_admin(interaction.user):
        return await interaction.response.send_message("❌NOT authorized.")
    await interaction.response.defer(thinking=True)

    try:
        res = admin_supabase.table("stats")\
                    .delete()\
                    .eq("name", name)\
                    .execute()
    except Exception as e:
        return await interaction.followup.send(f"❌ Delete failed: {e}")

    if not (res.data and len(res.data) > 0):
        return await interaction.followup.send(f"❌ No row found for `{name}` to delete.")
    
    await interaction.followup.send(f"🗑️ Row for `{name}` deleted.")

# —————————————————————————————
@tree.command(
    name="view_editors",
    description="List all current editors (admin only)"
)
async def view_editors(interaction: discord.Interaction):
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ You’re not authorized.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)

    try:
        res = admin_supabase.table("stats_editors_rights") \
                            .select("discord_id, discord_name, discriminator, added_at") \
                            .order("added_at", {"ascending": False}) \
                            .execute()
        rows = res.data or []
    except Exception as e:
        return await interaction.followup.send(
            f"❌ Failed to fetch editors: {e}", ephemeral=True
        )

    if not rows:
        return await interaction.followup.send("ℹ️ No editors found.", ephemeral=True)

    # Build a simple code block table
    lines = ["ID               | Name#Discriminator | Added At (UTC)"]
    lines.append("-" * len(lines[0]))
    for r in rows:
        ts = datetime.fromisoformat(r["added_at"]).strftime("%Y-%m-%d %H:%M")
        lines.append(
            f"{r['discord_id']:<16} | {r['discord_name']}#{r['discriminator']:<8} | {ts}"
        )

    table = "```" + "\n".join(lines) + "```"
    await interaction.followup.send(table, ephemeral=True)


# — add_editor — Admin only
@tree.command(
    name="add_editor",
    description="Grant someone editor rights (admin only)"
)
async def add_editor(interaction: discord.Interaction, member: discord.Member):
    if not is_admin(interaction.user):
        return await interaction.response.send_message("❌NOT authorized.", ephemeral=True)
    await interaction.response.defer(thinking=True)
    
    try:
        # capture name + discriminator + timestamp
        payload = {
            "discord_id": member.id,
            "discord_name": member.name,
            "discriminator": member.discriminator,
            # "added_at" uses default NOW() in Postgres if not specified
        }
        res = admin_supabase.table("stats_editors_rights")\
                            .insert(payload)\
                            .execute()
        # if the insert returns no data, it failed
        if not res.data:
            raise RuntimeError("Insert failed")
    except Exception as e:
        return await interaction.followup.send(f"❌ Failed to add editor: {e}")
    
    await interaction.followup.send(f"✅ {member.mention} can now view & update stats.", ephemeral=True)


# — remove_editor — Admin only
@tree.command(
    name="remove_editor",
    description="Revoke editor rights (admin only)"
)
async def remove_editor(interaction: discord.Interaction, member: discord.Member):
    if not is_admin(interaction.user):
        return await interaction.response.send_message("❌NOT authorized.", ephemeral=True)
    await interaction.response.defer(thinking=True)
    
    try:
        res = admin_supabase.table("stats_editors_rights") \
                            .delete() \
                            .eq("discord_id", member.id) \
                            .execute()
    # PostgREST returns an empty list if nothing was deleted
        if not res.data:
            return await interaction.followup.send(
                f"❌ {member.mention} was not an editor.", ephemeral=True
            )
    except Exception as e:
        return await interaction.followup.send(
            f"❌ Failed to remove editor: {e}", ephemeral=True
        )

    await interaction.followup.send(f"✅ {member.mention} can no longer view & update stats.", ephemeral=True)


# —————————————————————————————
@tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    # simply reply immediately
    latency_ms = round(bot.latency * 1000)
    await interaction.response.send_message(f"Pong! 🏓 {latency_ms}ms")


# —————————————————————————————
# — Run bot in background & WSGI —
def start_bot():
    bot.run(TOKEN)

# Start Discord in a background thread; Flask (Gunicorn) will serve the HTTP side.
threading.Thread(target=start_bot, daemon=True).start()