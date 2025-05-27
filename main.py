import os
import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask
from threading import Thread
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
# Flask Webserver (Gunicorn-compatible)
app = Flask(__name__)

@app.route("/")
def home():
    return "BOT is alive"

def run_webserver():
    app.run(host="0.0.0.0", port=3000)

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

    # Get only the needed rows
    page_data = load_page(sort_by, sort_desc, page)

    # Render lines
    lines = [HEADER, SEP]
    for row in page_data:
        lines.append(format_row(row))
        lines.append(blank_row())

    block = f"```css\n{chr(10).join(lines)}\n```"
    all_data = load_data()  # Needed for paginator logic
    view = TablePaginator(all_data, sort_by, sort_desc, page)

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
# Bot Run (Gunicorn runs Flask externally)
# Thread(target=run_webserver, daemon=True).start() #_NOT for production
bot.run(TOKEN)