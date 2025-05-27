#_main.py
import os
import threading
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask, request

from py.helpers import *
from py.paginator import TablePaginator



# ————————————————————————————————
# Env & token
TOKEN = os.getenv("DIS_TOKEN")
if not TOKEN: 
    raise RuntimeError("DIS_TOKEN missing")
TOKEN = TOKEN.strip()
print(f"✅ Loaded Discord token (length {len(TOKEN)})")

# ————————————————————————————————
def is_admin(user: discord.User) -> bool:
    return user.id in {762749123770056746, 1330770994138447892}  # replace with your admin IDs

# ————————————————————————————————
app = Flask(__name__)

@app.route("/", methods=["GET", "HEAD"])
def home():
    return "BOT is alive", 200

# ————————————————————————————————
# Discord Bot Setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user.name} ({bot.user.id})")

# ————————————————————————————————
# Slash Commands
@tree.command(name="show_table", description="Display table data with optional sorting & pagination")
@app_commands.describe(
    sort_by="Column to sort by (name, sing, dance, rally)",
    sort_desc="Sort descending? (default false)",
    page="Page number (default 1)"
)
async def show_table(
    interaction: discord.Interaction,
    sort_by: str = None,
    sort_desc: bool = False,
    page: int = 1
):
     # 1) Defer the response so Discord doesn’t timeout
    await interaction.response.defer(thinking=True)

    # 2) Do the slow operations
    if sort_by and sort_by.lower() not in ['name', 'sing', 'dance', 'rally']:
        return await interaction.response.send_message("❌ Invalid sort column")

    # Fetch only the rows needed for this page:
    page_data = load_page(sort_by, sort_desc, page)
    if not page_data:
        return await interaction.response.send_message("❌ Page out of range")

    # Build the table text block
    lines = [HEADER, SEP]
    for row in page_data:
        lines.append(format_row(row))
        lines.append(blank_row())
    block = f"```css\n{chr(10).join(lines)}\n```"

    # —————————————————————————
    # Instead of len(load_data()), load the full list:
    full_data = load_data()
    total = len(full_data)

    # Pass the list itself into the paginator, not just its length:
    view = TablePaginator(full_data, sort_by, sort_desc, page)

    # 3) Send with followup
    await interaction.followup.send(content=block, view=view)


@tree.command(name="update_table", description="Update a row in the table")
@app_commands.describe(name='Person name', sing='New sing', dance='New dance', rally='New rally')
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
            return await interaction.response.send_message(
                f"✅ Updated `{name}` with {' '.join(feedback)}"
            )
    await interaction.response.send_message(f"❌ No entry found for `{name}`")


@tree.command(name="add_row", description="Add a new row (admin only)")
async def add_row(interaction: discord.Interaction, name: str, sing: int, dance: int, rally: float):
    if not is_admin(interaction.user):
        return await interaction.response.send_message("❌ You are not authorized.")

    admin_supabase.table("stats").insert({
        "name": name, "sing": sing, "dance": dance, "rally": rally
    }).execute()

    invalidate_cache()
    await interaction.response.send_message(f"✅ Row for `{name}` added.")


@tree.command(name="delete_row", description="Delete a row (admin only)")
async def delete_row(interaction: discord.Interaction, name: str):
    # 1) Authoritation check
    if not is_admin(interaction.user):
        return await interaction.response.send_message("❌ You are not authorized.")

    # 2) Defer the response so we won’t hit the “Unknown interaction” timeout
    await interaction.response.defer(thinking=True)

    # 3) Perform the delete using the service_role client
    try:
        res = admin_supabase.table("stats").delete().eq("name", name).execute()
    except Exception as e:
        return await interaction.followup.send(f"❌ Delete failed: {e}")

    # 4) If no rows were deleted, res.data will be empty or None
    if not res.data:
        return await interaction.followup.send(f"❌ No row found for `{name}` to delete.")

    # 5) Invalidate our cache, then confirm to the user
    invalidate_cache()
    await interaction.followup.send(f"🗑️ Row for `{name}` deleted.")


# ————————————————————————————————
def start_bot():
    bot.run(TOKEN)

# Start Discord in a background thread; Flask (Gunicorn) will serve the HTTP side.
threading.Thread(target=start_bot, daemon=True).start()