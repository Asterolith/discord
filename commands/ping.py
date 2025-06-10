import discord
from discord import app_commands, Interaction, errors
from discord.ext import commands
from py.log_config import logger

@app_commands.command(
    name="ping",
    description="Check bot latency"
)
@app_commands.checks.cooldown(rate=1, per=5.0)
async def ping(interaction: Interaction):
    """Replies with round-trip latency in milliseconds."""
    latency_ms = round(interaction.client.latency * 1000)

    try:
        await interaction.response.send_message(f"Pong! 🏓 {latency_ms}ms")
    except discord.HTTPException as http_exc:
        # HTTP 429 o. ä.
        logger.warning("HTTPException beim ping: %s", http_exc, exc_info=True)
    except errors.InteractionResponded:
        try:
            await interaction.followup.send(f"Pong! 🏓 {latency_ms}ms")
        except Exception as exc:
            logger.error("Failed to follow up ping: %s", exc, exc_info=True)

def setup(bot: commands.Bot):
    bot.tree.add_command(ping)
