import os
import discord
from discord.ext import commands
from discord import app_commands, ui
from flask import Flask
from threading import Thread
from supabase import create_client, Client

# ————————————————————————————————
# Constants for Table Formatting
NAME_WIDTH = 15
SING_WIDTH = 7
DANCE_WIDTH = 7
RALLY_WIDTH = 7
ROWS_PER_PAGE = 25

# ————————————————————————————————
# Environment Variables
TOKEN = os.getenv("DIS_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not TOKEN or not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Missing required environment variables!")
    exit(1)

TOKEN = TOKEN.strip()
print(f"✅ Loaded Discord token (length {len(TOKEN)})")

# ————————————————————————————————
# Supabase Client Setup
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ————————————————————————————————
# Helper Functions
def load_data():
    res = supabase.table("stats").select("*").execute()
    return res.data or []


def update_row(name, **kwargs):
    update_data = {k: v for k, v in kwargs.items() if v is not None}
    if update_data:
        supabase.table("stats").update(update_data).eq("name", name).execute()


def format_header():
    return (
        f"{'Name':<{NAME_WIDTH}} | "
        f"{'Sing[k]':<{SING_WIDTH}} | "
        f"{'Dance[k]':<{DANCE_WIDTH}} | "
        f"{'Rally[Mio]':<{RALLY_WIDTH}}"
    )


def format_row(d):
    # Ensure numeric fields default to 0 if None
    name = f"{d.get('name',''):<{NAME_WIDTH}}"
    sing = d.get('sing') if d.get('sing') is not None else 0
    dance = d.get('dance') if d.get('dance') is not None else 0
    rally = d.get('rally') if d.get('rally') is not None else 0
    return (
        f"{name:<{NAME_WIDTH}} | "
        f"{sing:<{SING_WIDTH}} | "
        f"{dance:<{DANCE_WIDTH}} | "
        f"{rally:<{RALLY_WIDTH}}"
    )

    # separator = "-" * len(header)

    # rows = []
    # for d in data:
    #     name_col = f"{d['name']:<{NAME_WIDTH}}"
    #     sing_col = f"{d['sing'] or 0:<{SING_WIDTH}}"
    #     dance_col = f"{d['dance'] or 0:<{DANCE_WIDTH}}"
    #     rally_col = f"{d['rally'] or 0:<{RALLY_WIDTH}}"
    #     rows.append(f"{name_col} | {sing_col} | {dance_col} | {rally_col}")

    # return "\n".join([header, separator] + rows)

def sort_data(data, column: str, descending: bool = False):
    def key_fn(row):
        val = row.get(column)
        return val if val is not None else ("" if column == "name" else -999999)
    return sorted(data, key=key_fn, reverse=descending)

# ————————————————
# Paginator View
typedef = ui.View
class TablePaginator(ui.View):
    def __init__(self, data, sort_by: str, sort_desc: bool, page: int):
        super().__init__(timeout=120)
        self.data = data
        self.sort_by = sort_by
        self.sort_desc = sort_desc
        self.page = page
        self.update_buttons()

    def update_buttons(self):
        max_pages = max(1, (len(self.data) - 1) // ROWS_PER_PAGE + 1)
        self.prev_button.disabled = self.page <= 1
        self.next_button.disabled = self.page >= max_pages

    @ui.button(label='◀ Prev', style=discord.ButtonStyle.primary, custom_id='prev')
    async def prev_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.change_page(interaction, self.page - 1)

    @ui.button(label='Next ▶', style=discord.ButtonStyle.primary, custom_id='next')
    async def next_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.change_page(interaction, self.page + 1)

    async def change_page(self, interaction: discord.Interaction, new_page: int):
        self.page = new_page
        # re-sort
        data = sort_data(self.data, self.sort_by, self.sort_desc) if self.sort_by else self.data
        # paginate
        start = (self.page - 1) * ROWS_PER_PAGE
        page_data = data[start:start + ROWS_PER_PAGE]
        # re-render
        lines = [format_header(), '-' * len(format_header())]
        for row in page_data:
            lines.append(format_row(row))
            lines.append('')
        block = '```css\n' + '\n'.join(lines) + '\n```'
        self.update_buttons()
        await interaction.response.edit_message(content=block, view=self)

# ————————————————
# Flask Keep-Alive Webserver
app = Flask("")
@app.route("/")
def home():
    return "BOT is alive"

def run_webserver():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))

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
    # paginate
    start = (page-1)*ROWS_PER_PAGE
    page_data = data[start:start+ROWS_PER_PAGE]
    if not page_data:
        return await interaction.response.send_message('❌ Page out of range')
    # initial render
    lines = [format_header(), '-'*len(format_header())]
    for row in page_data:
        lines.append(format_row(row))
        lines.append('')
    block = '```css\n' + '\n'.join(lines) + '\n```'
    view = TablePaginator(data, sort_by, sort_desc, page)
    await interaction.response.send_message(content=block, view=view)


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
    found = False

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
Thread(target=run_webserver, daemon=True).start()
bot.run(TOKEN)