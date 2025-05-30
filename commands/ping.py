# commands/ping.py
import discord
from discord import app_commands, Interaction

@discord.app_commands.command(name="ping", description="Check bot latency")
async def ping(interaction: Interaction):
    latency_ms = round(interaction.client.latency * 1000)
    try:
        # first attempt: the “normal” response
        await interaction.response.send_message(f"Pong! 🏓 {latency_ms}ms")
    except discord.errors.InteractionResponded:
        # if somehow we already replied/deferred, use followup
        await interaction.followup.send(f"Pong! 🏓 {latency_ms}ms")

def setup(bot):
    bot.tree.add_command(ping)