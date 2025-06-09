# bot.py
import os, asyncio, logging
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

# Health-Check endpoint
async def handle_health(request):
    return web.Response(text="OK", status=200)


async def start_web(runner, port):
    site = web.TCPSite(runner, "0.0.0.0", port)
    await runner.setup()
    await site.start()
    logger.info(f"🌐 Health-Endpoint running on port {port}")


async def shutdown_web(runner):
    logger.info("🌐 Shutting down health-server…")
    await runner.cleanup()


async def main():
    # 1) HTTP-App und Runner anlegen
    app = web.Application()
    app.router.add_get("/", handle_health)
    runner = web.AppRunner(app)

    # 2) parallel starten
    web_task = asyncio.create_task(start_web(runner, int(os.getenv("PORT", 5000))))
    bot_task = asyncio.create_task(bot.start(os.environ["DIS_TOKEN"]))

    # 3) warten bis der Bot stoppt (z.B. KeyboardInterrupt)
    done, pending = await asyncio.wait(
        [bot_task],
        return_when=asyncio.FIRST_COMPLETED
    )

    # 4) wenn BotTask fertig, sauber HTTP herunterfahren
    await shutdown_web(runner)

    # 5) ggf. den Web-Task abbrechen
    web_task.cancel()
    try:
        await web_task
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("✋ Shutdown requested, exiting…")