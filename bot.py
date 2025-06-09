# bot.py
import os
import signal
import asyncio
import logging

import discord
from discord.ext import commands
from aiohttp import web

from py.log_config import root_logger as logger
from commands.show_table    import setup as setup_show
from commands.update_table  import setup as setup_update
from commands.manage_row    import setup as setup_row
from commands.manage_editor import setup as setup_editor
from commands.ping          import setup as setup_ping

# ─── Bot Setup ──────────────────────────────────────────────────────────────
intents = discord.Intents.default()
bot     = commands.Bot(command_prefix="!", intents=intents)

def register_commands():
    setup_show(bot)
    setup_update(bot)
    setup_row(bot)
    setup_editor(bot)
    setup_ping(bot)

register_commands()

@bot.event
async def on_ready():
    await bot.tree.sync()
    logger.info(f"✅ Bot ready: {bot.user} ({bot.user.id})")

# ─── HTTP Health-Server Setup ─────────────────────────────────────────────────
_health_app   = web.Application()
_health_app.add_routes([web.get("/", lambda req: web.Response(text="OK", status=200))])
_runner       = web.AppRunner(_health_app)
_site         = None

async def start_webserver():
    global _site
    await _runner.setup()
    port = int(os.getenv("PORT", 5000))
    _site = web.TCPSite(_runner, "0.0.0.0", port)
    await _site.start()
    logger.info(f"🌐 Health-Server läuft auf Port {port}")

async def shutdown_webserver():
    logger.info("🛑 Shutting down health server…")
    if _site:
        await _site.stop()
    await _runner.cleanup()

# ─── Graceful Shutdown ───────────────────────────────────────────────────────
async def shutdown(signal_name):
    logger.info(f"Received {signal_name}, shutting down…")
    await shutdown_webserver()
    await bot.close()
    asyncio.get_event_loop().stop()

# ─── Main: Web + Bot parallel ────────────────────────────────────────────────
async def main():
    # Register OS-Signals
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s.name)))
    # Start HTTP & Bot
    await start_webserver()
    await bot.start(os.environ["DIS_TOKEN"])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt, exiting…")
