# main.py
import os
import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask
from threading import Thread
import json

# ————————————————
# Bot Token from Replit Secret
raw_token = os.getenv("DIS_TOKEN")
if not raw_token:
    print("❌ ERROR: DIS_TOKEN env var not found or empty!")
    exit(1)
TOKEN = raw_token.strip()
print(f"✅ Loaded token (length {len(TOKEN)})")

DATA_FILE = 'stats.json'

# Create default data file if it doesn't exist
default_data = [
    {"name": "name 1", "sing": 200, "dance": 200, "rally": 0.0},
    {"name": "name 2", "sing": 150, "dance": 150, "rally": 0.0},
    {"name": "name 3", "sing": 0, "dance": 0, "rally": 0.0}
]


if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump(default_data, f, indent=4)

def load_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# ————————————————
# Flask “Keep-Alive” Webserver
app = Flask("")

@app.route("/")
def home():
    return "Bot is alive"

def run_webserver():
    app.run(host="0.0.0.0", port=3000)

# ————————————————
# Discord-Bot setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    # Sync the slash commands to Discord
    await tree.sync()
    print(f'Logged in as {bot.user.name} ({bot.user.id})')

@tree.command(name="show_table", description="Display current table data (code block style)")
async def show_table(interaction: discord.Interaction):
    data = load_data()

    #_1.Define fixed column widths
    #_Adjust these numbers to fit your longest “name” or number of digits
    NAME_WIDTH  = 15
    SING_WIDTH  = 7
    DANCE_WIDTH = 7
    RALLY_WIDTH = 7

    #_2.Build header row with padding
    header = (
        f"{'Name':<{NAME_WIDTH}} | "
        f"{'Sing[k]':<{SING_WIDTH}} | "
        f"{'Dance[k]':<{DANCE_WIDTH}} | "
        f"{'Rally[Mio]':<{RALLY_WIDTH}}"
    )
    separator = "-" * len(header)

    #_3.Build each data row with same padding
    rows = []
    for d in data:
        name_col = f"{d['name']:<{NAME_WIDTH}}"
        sing_col = f"{d['sing']:<{SING_WIDTH}}"
        dance_col = f"{d['dance']:<{DANCE_WIDTH}}"
        rally_col = f"{d['rally']:<{RALLY_WIDTH}}"
        rows.append(f"{name_col} | {sing_col} | {dance_col} | {rally_col}")

    #_4.Join headerm separator and rows, then wrap in code block
    table_text = "\n".join([header, separator] + rows)

    # 5) If it fits under 2000 chars, send as a code block; otherwise, send as a .txt file
    if len(table_text) <= 1990:
        # Wrapping in triple backticks so Discord renders it as a code block
        await interaction.response.send_message(f"```{table_text}```")
    else:
        # Write to a temporary file and send that instead
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
            if sing is not None:
                row["sing"] = sing
            if dance is not None:
                row["dance"] = dance
            if rally is not None:
                row["rally"] = rally
            found = True
            break

    if found:
        save_data(data)
        await interaction.response.send_message(
            f"✅ Updated `{name}` with values: sing={sing}, dance={dance}, rally={rally}"
        )
    else:
        await interaction.response.send_message(f"❌ No entry found for `{name}`")

# ————————————————
# Start the Flask server in a thread, then run the bot
Thread(target=run_webserver).start()
bot.run(TOKEN)