# bot.py
import os
import logging
import discord
from discord.ext import commands
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


bot.run(os.environ["DIS_TOKEN"])

logger.info("✨ Discord-Bot stopped.")

# EOF