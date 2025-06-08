# commands/manage_row.py

import discord
from discord import app_commands, Interaction, errors
from discord.ext import commands

from py.helpers import is_admin, admin_supabase
from py.log_config import logger

# ─── add_row ────────────────────────────────────────────────────────────────────
@app_commands.command(
    name="add_row",
    description="Add a new stats row (admin only)"
)
async def add_row(
    interaction: Interaction,
    name: str,
    sing: int,
    dance: int,
    rally: float
):
    user = interaction.user
    if not is_admin(user):
        return await interaction.response.send_message(
            "❌ You’re not authorized.",
            ephemeral=True
        )

    # Defer so we can follow up
    try:
        await interaction.response.defer(thinking=True)
    except errors.InteractionResponded:
        pass

    # Insert
    try:
        res = admin_supabase.table("stats") \
                            .insert({
                                "name": name,
                                "sing": sing,
                                "dance": dance,
                                "rally": rally
                            }).execute()
        if not res.data:
            raise RuntimeError("No rows inserted")
    except Exception as exc:
        logger.error("Error inserting row %s: %s", name, exc, exc_info=True)
        return await interaction.followup.send(
            f"❌ Failed to add `{name}`. Please check logs.",
            ephemeral=True
        )

    await interaction.followup.send(f"✅ Row for `{name}` added.")


# ─── delete_row ─────────────────────────────────────────────────────────────────
@app_commands.command(
    name="delete_row",
    description="Delete a stats row (admin only)"
)
async def delete_row(
    interaction: Interaction,
    name: str
):
    user = interaction.user
    if not is_admin(user):
        return await interaction.response.send_message(
            "❌ You’re not authorized.",
            ephemeral=True
        )

    try:
        await interaction.response.defer(thinking=True)
    except errors.InteractionResponded:
        pass

    try:
        res = admin_supabase.table("stats") \
                            .delete() \
                            .eq("name", name) \
                            .execute()
        if not res.data:
            return await interaction.followup.send(
                f"❌ No entry found for `{name}`.",
                ephemeral=True
            )
    except Exception as exc:
        logger.error("Error deleting row %s: %s", name, exc, exc_info=True)
        return await interaction.followup.send(
            f"❌ Failed to delete `{name}`. Please check logs.",
            ephemeral=True
        )

    await interaction.followup.send(f"🗑️ Row for `{name}` deleted.")


# ─── Registration ───────────────────────────────────────────────────────────────
def setup(bot: commands.Bot):
    bot.tree.add_command(add_row)
    bot.tree.add_command(delete_row)