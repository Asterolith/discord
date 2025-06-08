# commands/ping.py

import discord
from discord import app_commands, Interaction, errors
from discord.ext import commands
from py.log_config import logger

@app_commands.command(
    name="ping",
    description="Check bot latency"
)
async def ping(interaction: Interaction):
    """Replies with round-trip latency in milliseconds."""
    latency_ms = round(interaction.client.latency * 1000)

    # No need to defer here—this is a quick response.
    try:
        await interaction.response.send_message(f"Pong! 🏓 {latency_ms}ms")
    except errors.InteractionResponded:
        # If we've somehow already responded, fall back to followup
        try:
            await interaction.followup.send(f"Pong! 🏓 {latency_ms}ms")
        except Exception as exc:
            logger.error("Failed to follow up ping: %s", exc, exc_info=True)

def setup(bot: commands.Bot):
    bot.tree.add_command(ping)
