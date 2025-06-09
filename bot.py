# bot.py

import os, asyncio
import discord
from discord.ext import commands
from aiohttp import web
from py.log_config import logger

# Slash-Commands registrieren …
from commands.show_table    import setup as setup_show
from commands.update_table  import setup as setup_update
from commands.manage_row    import setup as setup_row
from commands.manage_editor import setup as setup_editor
from commands.ping          import setup as setup_ping

logger.info("✨ Starting Discord-Bot…")
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Commands einbinden
for setup in (setup_show, setup_update, setup_row, setup_editor, setup_ping):
    setup(bot)

@bot.event
async def on_ready():
    await bot.tree.sync()
    logger.info(f"✅ Bot ready: {bot.user} ({bot.user.id})")

async def handle_health(request):
    return web.Response(text="OK", status=200)

async def start_web():
    app = web.Application()
    app.add_routes([web.get("/", handle_health)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 5000)))
    await site.start()
    logger.info("🌐 Health server running")

async def main():
    await asyncio.gather(start_web(), bot.start(os.environ["DIS_TOKEN"]))

if __name__ == "__main__":
    asyncio.run(main())