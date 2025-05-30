#_main.py
import os, threading
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask, request
from datetime import datetime

from py.helpers import (
    user_client_for, admin_supabase,
    is_admin,
    ROWS_PER_PAGE, HEADER, SEP,
    load_data, sort_data,
    format_row, blank_row
)
from py.paginator import TablePaginator

# —————————————————————————————
# — Env & Discord token —
TOKEN = os.getenv("DIS_TOKEN", "").strip()
if not TOKEN:
    raise RuntimeError("DIS_TOKEN missing")
print(f"✅ Discord token length: {len(TOKEN)}")


# —————————————————————————————
# — Discord bot setup —
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

app = Flask(__name__)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user.name} ({bot.user.id})")

# this keeps Render happy
@app.route('/')
def index():
    return "Bot is running!"


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
                     sort_desc: bool = True,
                     page: int = 1):
    # Try to defer, but if it’s “unknown,” ignore it
    try:
        await interaction.response.defer(thinking=True)
    except discord.errors.NotFound:
        pass

    # 2) Validate
    sort_by = sort_by.lower() if sort_by else None
    if sort_by and sort_by not in ('name','sing','dance','rally'):
        return await interaction.followup.send('❌ Invalid sort column')

    # 3) Pull & sort locally
    if is_admin(interaction.user):
        full = admin_supabase.table('stats').select('*').execute().data or []
    else:
        full = load_data()    # uses anon & cache

    if sort_by:
        full = sort_data(full, sort_by, sort_desc)

   # 4) Slice page
    start = (page-1)*ROWS_PER_PAGE
    page_data = full[start:start+ROWS_PER_PAGE]
    if not page_data:
        return await interaction.followup.send('❌ Page out of range')

    # 5) Build text block
    lines = [HEADER, SEP]
    for r in page_data:
        lines.append(format_row(r)); lines.append(blank_row())
    block = f"```css\n{chr(10).join(lines)}\n```"

    # 6) Build paginator view with the full list, so it knows max pages
    view = TablePaginator(full, sort_by, sort_desc, page)

    try:
        await interaction.response.edit_message(content=block, view=view)
    except discord.errors.NotFound:
        # fallback to editing the original followup
        await interaction.followup.edit_message(
        message_id=interaction.message.id,
        content=block,
        view=view
        )


# — update_table —
@tree.command(name="update_table", description="Update a stats row (editor)")
@app_commands.describe(name='Entry name', sing='New sing value', dance='New dance value', rally='New rally value')
async def update_table(interaction: discord.Interaction,
                       name: str,
                       sing: int,
                       dance: int,
                       rally: float = None):
    await interaction.response.defer(thinking=True)

    if is_admin(interaction.user):
        client = admin_supabase    # uses your service_role key, bypasses RLS
    else:
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
    # 1) Authorization
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ You’re not authorized.", ephemeral=True)
        return

    # 2) Defer before the DB hit
    await interaction.response.defer(thinking=True)

    # 3) Fetch all rows (no .order() here)
    try:
        res = admin_supabase.table("stats_editors_rights") \
                           .select("discord_id, discord_name, added_at") \
                           .execute()
        rows = res.data or []
    except Exception as e:
        return await interaction.followup.send(f"❌ Failed to fetch editors: {e}", ephemeral=True)

    # 4) Sort descending by ‘added_at’ in Python
    try:
        rows.sort(key=lambda r: r["added_at"], reverse=True)
    except KeyError:
        # if added_at missing, just leave as-is
        pass

    if not rows:
        return await interaction.followup.send("ℹ️ No editors found.", ephemeral=True)

    # 5) Build a monospace table
    header = "ID               | Name | Added At (UTC)"
    sep    = "-" * len(header)
    lines  = [header, sep]

    for r in rows:
        ts = datetime.fromisoformat(r['added_at']).strftime("%Y-%m-%d %H:%M")
        lines.append(
            f"{r['discord_id']:<16} | {r['discord_name']:<32} | {ts}"
        )

    table = "```" + "\n".join(lines) + "```"

    # 6) Send it
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
def run_bot():
    bot.run(TOKEN)

# Start Discord in a background thread; Flask (Gunicorn) will serve the HTTP side.
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))