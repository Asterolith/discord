#_bot.py: core Discord bot, loads commands

import os
import logging
import discord
from discord.ext import commands

# Initialize logging (config in py/log_config)
from py.log_config import root_logger as logger
logger.info("Discord bot starting…")
logger.info("🐬 Logflare integration is live!")

# Import command modules
from commands.show_table import setup as setup_show
from commands.update_table import setup as setup_update
from commands.manage_row import setup as setup_row
from commands.manage_editor import setup as setup_editor
from commands.ping import setup as setup_ping


# Create bot instance
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Register slash commands
def register_commands():
    setup_show(bot)
    setup_update(bot)
    setup_row(bot)
    setup_editor(bot)
    setup_ping(bot)

register_commands()


@bot.event
async def on_ready():
    # Sync commands on startup
    await bot.tree.sync()
    logger.info(f"✅ Bot ready: {bot.user} ({bot.user.id})")

if __name__ == "__main__":
    token = os.getenv("DIS_TOKEN")
    if not token:
        logger.error("DIS_TOKEN missing")
        raise RuntimeError("DIS_TOKEN missing")
    bot.run(token)

# Export bot for web boot
__all__ = ["bot"]