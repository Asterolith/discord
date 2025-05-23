import os
import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask
from threading import Thread
from supabase import create_client, Client

# ————————————————
# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Missing Supabase environment variables!")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ————————————————
# Bot Token
raw_token = os.getenv("DIS_TOKEN")
if not raw_token:
    print("❌ ERROR: DIS_TOKEN env var not found or empty!")
    exit(1)

TOKEN = raw_token.strip()
print(f"✅ Loaded token (length {len(TOKEN)})")

# ————————————————
# Supabase data helpers
def load_data():
    res = supabase.table("stats").select("*").execute()
    return res.data

def update_row(name, sing, dance, rally):
    supabase.table("stats").update({
        "sing": sing,
        "dance": dance,
        "rally": rally
    }).eq("name", name).execute()

# ————————————————
# Flask Keep-Alive Webserver
app = Flask("")
@app.route("/")
def home():
    return "BOT is alive"

def run_webserver():
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)

# ————————————————
# Discord bot setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    await tree.sync()
    print(f'Logged in as {bot.user.name} ({bot.user.id})')


@tree.command(name="show_table", description="Display current table data (code block style)")
async def show_table(interaction: discord.Interaction):
    data = load_data()

    NAME_WIDTH  = 15
    SING_WIDTH  = 7
    DANCE_WIDTH = 7
    RALLY_WIDTH = 7

    header = (
        f"{'Name':<{NAME_WIDTH}} | "
        f"{'Sing[k]':<{SING_WIDTH}} | "
        f"{'Dance[k]':<{DANCE_WIDTH}} | "
        f"{'Rally[Mio]':<{RALLY_WIDTH}}"
    )
    separator = "-" * len(header)

    rows = []
    for d in data:
        name_col = f"{d['name']:<{NAME_WIDTH}}"
        sing_col = f"{d['sing']:<{SING_WIDTH}}"
        dance_col = f"{d['dance']:<{DANCE_WIDTH}}"
        rally_col = f"{d['rally']:<{RALLY_WIDTH}}"
        rows.append(f"{name_col} | {sing_col} | {dance_col} | {rally_col}")

    table_text = "\n".join([header, separator] + rows)

    if len(table_text) <= 1990:
        await interaction.response.send_message(f"```{table_text}```")
    else:
        tmp = "table.txt"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(table_text)
        await interaction.response.send_message(
            content="Table is too large to show directly, here’s a text file:",
            file=discord.File(tmp)
        )

@tree.command(name="update_table", description="Update table data")
@app_commands.describe(
    name="The name of the person to update",
    sing="New value for sing (required)",
    dance="New value for dance (required)",
    rally="New value for rally (optional)"
)
async def update_table(
    interaction: discord.Interaction,
    name: str,
    sing: int,
    dance: int,
    rally: float = None
):
    data = load_data()
    found = False

    for row in data:
        if row["name"].lower() == name.lower():
            update_row(name, sing, dance, rally if rally is not None else row['rally'])
            found = True
            break

    if found:
        await interaction.response.send_message(
            f"✅ Updated `{name}` with values: sing={sing}, dance={dance}, rally={rally}"
        )
    else:
        await interaction.response.send_message(f"❌ No entry found for `{name}`")

# ————————————————
# Start webserver and bot
Thread(target=run_webserver, daemon=True).start()
bot.run(TOKEN)