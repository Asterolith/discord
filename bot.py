# bot.py
import os, asyncio, logging
import discord
from discord.ext import commands
from aiohttp import web

from py.log_config import logger
#_slash command-setup functions:
from commands.show_table    import setup as setup_show
from commands.ping          import setup as setup_ping
from commands.update_table  import setup as setup_update
from commands.manage_row    import setup as setup_manage_row
from commands.manage_editor import setup as setup_manage_editor

logger.info("✨ Starting Discord Bot…")

intents = discord.Intents.default()
intents.message_content = True  # if slash commands silently fail
bot = commands.Bot(command_prefix="!", intents=intents)

# Register all slash commands once
for setup_func in (
    setup_show,
    setup_ping,
    setup_update,
    setup_manage_row,
    setup_manage_editor,
):
    setup_func(bot)


@bot.event
async def on_ready():
    await bot.tree.sync()
    logger.info(f"✅ Bot ready: {bot.user} ({bot.user.id})")


# — Health endpoint (for UptimeRobot, etc.) —
async def handle_health(request: web.Request) -> web.Response:
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
    # await asyncio.Event().wait()  # Keeps the health server running forever


async def main():
    health_task = asyncio.create_task(start_health())

    for attempt in range(5):
        try:
            await bot.start(os.environ["DIS_TOKEN"])
            break  # wenn Start erfolgreich, kein Retry
        except discord.HTTPException as e:
            if e.status == 429:
                wait = 2 ** attempt
                logger.warning(f"Rate limited. Retrying in {wait}s...")
                await asyncio.sleep(wait)
            else:
                raise
        finally:
            # Wichtig: Aufräumen, sonst kommt das "Unclosed client session"-Warning
            if bot.is_closed():
                await bot.close()

    await health_task  # wartet auf Health-Server (quasi ewig)


if __name__ == "__main__":
    asyncio.run(main())