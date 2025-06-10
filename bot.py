import os, asyncio, logging
import discord
from discord.ext import commands
from aiohttp import web
from py.log_config import logger
from commands.show_table    import setup as setup_show
from commands.ping          import setup as setup_ping
from commands.update_table  import setup as setup_update
from commands.manage_row    import setup as setup_row
from commands.manage_editor import setup as setup_editor

logger.info("✨ Starting Discord Bot…")
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Register slash commands
for fn in (setup_show, setup_ping, setup_update, setup_row, setup_editor):
    fn(bot)

@bot.event
async def on_ready():
    await bot.tree.sync()
    logger.info(f"✅ Bot ready: {bot.user} ({bot.user.id})")

# Simple health-check endpoint
async def handle_health(req):
    return web.Response(text="OK")

async def start_health():
    app = web.Application()
    app.router.add_get("/", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 5000)))
    await site.start()
    logger.info("🌐 Health server running")

async def main():
    # Run health server and bot in parallel
    await asyncio.gather(
        start_health(),
        bot.start(os.environ["DIS_TOKEN"])
    )

if __name__ == "__main__":
    asyncio.run(main())
