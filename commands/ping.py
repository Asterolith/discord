# commands/ping.py
from discord import app_commands, Interaction

@app_commands.command(name="ping", description="Check bot latency")
async def ping(interaction: Interaction):
    # use interaction.client instead of a fresh bot
    latency_ms = round(interaction.client.latency * 1000)
    await interaction.response.send_message(f"Pong! 🏓 {latency_ms}ms")

def setup(bot):
    bot.tree.add_command(ping)