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
# Create Flask
app = Flask(__name__)

# Wrap Flask’s WSGI app so that any request without a Host header
# gets “localhost” as a fallback. This prevents Werkzeug from doing
# `None.encode("idna")`.
_original_wsgi = app.wsgi_app
def _wsgi_with_default_host(environ, start_response):
    if not environ.get("HTTP_HOST"):
        # If Render’s health checker didn’t set a Host, give it “localhost”.
        environ["HTTP_HOST"] = "localhost"
    return _original_wsgi(environ, start_response)

app.wsgi_app = _wsgi_with_default_host
# —————————————
# Your “/” route (or /health)
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

# ————————————————
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

    await interaction.response.send_message(content=block, view=view)


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

# ————————————————

def start_bot():
    bot.run(TOKEN)

# Start Discord in a background thread; Flask (Gunicorn) will serve the HTTP side.
threading.Thread(target=start_bot, daemon=True).start()