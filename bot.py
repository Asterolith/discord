# bot.py
import os
import logging
import discord
from discord.ext import commands

from py.log_config import logger
from commands.show_table    import setup as setup_show
from commands.ping          import setup as setup_ping
from commands.update_table  import setup as setup_update
from commands.manage_row    import setup as setup_manage_row
from commands.manage_editor import setup as setup_manage_editor

logger.info("✨ Starting Discord Bot…")

intents = discord.Intents.default()
intents.message_content = True  # nötig für Slash-Commands
bot = commands.Bot(command_prefix="!", intents=intents)

# Slash-Commands registrieren
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

if __name__ == "__main__":
    token = os.getenv("DIS_TOKEN")
    if not token:
        logger.error("DIS_TOKEN missing")
        raise RuntimeError("DIS_TOKEN missing")
    bot.run(token)
