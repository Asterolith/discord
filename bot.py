#_bot.py: core Discord bot, loads commands
import os
import discord
from discord.ext import commands

from commands import (
    show_table, update_table,
    manage_row, manage_editor, ping
)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# register all command modules
for module in (
    show_table, update_table,
    manage_row, manage_editor, ping
):
    module.setup(bot)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot ready: {bot.user} ({bot.user.id})")

if __name__ == "__main__":
    token = os.getenv("DIS_TOKEN")
    if not token:
        raise RuntimeError("DIS_TOKEN missing")
    bot.run(token)


# Export bot so it can be used in tests if needed
__all__ = ["run_bot"]