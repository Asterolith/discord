# bot.py

import os
import asyncio
import logging

import discord
from discord.ext import commands
from aiohttp import web

# Logging initialisieren (py/log_config konfiguriert root_logger)
from py.log_config import root_logger as logger

logger.info("Discord bot starting…")
logger.info("🐬 Logflare integration is live!")

# Slash-Command Module
from commands.show_table    import setup as setup_show
from commands.update_table  import setup as setup_update
from commands.manage_row    import setup as setup_row
from commands.manage_editor import setup as setup_editor
from commands.ping          import setup as setup_ping

# ─── Discord Bot Setup ───────────────────────────────────────────────────────
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

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

# ─── Health-Endpoint mit aiohttp ─────────────────────────────────────────────
async def handle_health(request: web.Request) -> web.Response:
    return web.Response(text="OK", status=200)

async def start_webserver():
    app = web.Application()
    app.add_routes([web.get("/", handle_health)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 5000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🌐 Webserver started on port {port}")

# ─── Main: Web + Bot parallel ────────────────────────────────────────────────
async def main():
    await start_webserver()           # Health-Check starten
    await bot.start(os.environ["DIS_TOKEN"])  # Discord-Bot

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down…")
