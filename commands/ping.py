
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix="!")

@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    # simply reply immediately
    await interaction.response.send_message(f"Pong! 🏓 {round(bot.latency*1000)}ms")


def setup(bot: commands.Bot):
    bot.tree.add_command(ping)
