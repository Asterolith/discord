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
if not TOKEN: raise RuntimeError("DIS_TOKEN missing")
TOKEN = TOKEN.strip()
print(f"✅ Loaded Discord token (length {len(TOKEN)})")

# ————————————————————————————————
# Flask Keep-Alive Webserver
def run_webserver():
    # from flask import Flask
    app = Flask("")
    @app.route("/")
    def home(): return "BOT is alive"
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',3000)))
Thread(target=run_webserver,daemon=True).start()

# ————————————————
# Discord Bot Setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user.name} ({bot.user.id})")

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
    data = load_data()

    if sort_by:
        col = sort_by.lower()
        if col in ['name','sing','dance','rally']:
            data = sort_data(data, col, sort_desc)
        else:
            return await interaction.response.send_message('❌ Invalid sort column')

    paginator=TablePaginator(data, sort_by, sort_desc, page)
    #_init render
    start = (page - 1) * ROWS_PER_PAGE
    page_data = data[start:start + ROWS_PER_PAGE]
    lines = [format_header(), '-' * len(format_header())]
    for row in page_data:
        lines.append(format_row(row))
        lines.append(blank_row())

    block = '```css\n' + '\n'.join(lines) + '\n```'
    await interaction.response.send_message(content=block, view=paginator)


    # if len(table_text) <= 1990:
    #     await interaction.response.send_message(f"```{table_text}```")
    # else:
    #     tmp = "table.txt"
    #     with open(tmp, "w", encoding="utf-8") as f:
    #         f.write(table_text)
    #     await interaction.response.send_message(
    #         content="Table is too large to show directly, here’s a text file:",
    #         file=discord.File(tmp)
    #     )


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
# Start webserver and bot
# Thread(target=run_webserver, daemon=True).start()
bot.run(TOKEN)