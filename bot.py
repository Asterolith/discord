# bot.py
import os
import asyncio
import signal
import logging

import discord
from discord.ext import commands
from aiohttp import web

from py.log_config import logger
from commands.show_table    import setup as setup_show
from commands.update_table  import setup as setup_update
from commands.manage_row    import setup as setup_manage_row
from commands.manage_editor import setup as setup_manage_editor
from commands.ping          import setup as setup_ping

logger.info("✨ Starting Discord Bot…")

# — Discord-Bot Setup —
intents = discord.Intents.default()
intents.message_content = True  # nötig für Slash-Commands
bot = commands.Bot(command_prefix="!", intents=intents)

# Slash-Commands registrieren
for setup in (setup_show, setup_update, setup_manage_row, setup_manage_editor, setup_ping):
    setup(bot)

@bot.event
async def on_ready():
    await bot.tree.sync()
    logger.info(f"✅ Bot ready: {bot.user} ({bot.user.id})")

# — Health-Endpoint —
async def handle_health(request: web.Request) -> web.Response:
    return web.Response(text="OK", status=200)

async def start_health_server():
    app = web.Application()
    app.router.add_get("/", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 5000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🌐 Health server running on port {port}")
    # halte den Server am Leben
    await asyncio.Event().wait()

# — Clean Shutdown —
def setup_signal_handlers(loop):
    async def _shutdown():
        logger.info("✋ Shutdown signal received, closing bot…")
        await bot.close()
        loop.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(_shutdown()))

# — Main mit Rate-Limit-Retry und Back-off —
async def main():
    # Signal-Handler registrieren
    loop = asyncio.get_running_loop()
    setup_signal_handlers(loop)

    async def run_bot_with_backoff():
        delay = 1
        for attempt in range(6):
            try:
                await bot.start(os.environ["DIS_TOKEN"])
                return
            except discord.HTTPException as e:
                if e.status == 429:
                    logger.warning(f"Rate limited; retrying in {delay}s…")
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    logger.error("Critical Discord error", exc_info=e)
                    raise
        logger.error("Failed to start bot after retries")
        await bot.close()

    # Starte Health-Server und Bot parallel
    await asyncio.gather(
        start_health_server(),
        run_bot_with_backoff(),
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error("Fatal error in main()", exc_info=e)
