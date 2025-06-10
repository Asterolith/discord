# bot.py
import os, asyncio, logging
import discord
from discord.ext import commands
from aiohttp import web
# dein Log-Setup
from py.log_config import logger

# Slash-Commands importieren …
from commands.show_table    import setup as setup_show
from commands.ping          import setup as setup_ping
from commands.update_table  import setup as setup_update
from commands.manage_row    import setup as setup_manage_row
from commands.manage_editor import setup as setup_manage_editor

logger.info("✨ Starting Discord Bot…")
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# Befehle registrieren
for setup in (setup_show, setup_ping, setup_update, setup_manage_row, setup_manage_editor):
    setup(bot)

@bot.event
async def on_ready():
    await bot.tree.sync()
    logger.info(f"✅ Bot ready: {bot.user} ({bot.user.id})")

# Health-Endpoint
async def handle_health(request):
    return web.Response(text="OK", status=200)

async def start_health():
    app = web.Application()
    app.router.add_get("/", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 5000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🌐 Health server running on port {port}")
    await runner.cleanup()

async def main():
    # Health + Bot parallel starten, aber nur EIN Bot-Start
    await asyncio.gather(
        start_health(),
        bot.start(os.environ["DIS_TOKEN"])
    )

if __name__ == "__main__":
    asyncio.run(main())
