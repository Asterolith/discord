from discord import app_commands, Interaction
from discord.ext import commands
from py.helpers import is_admin, is_editor, admin_supabase
from py.log_config import logger

@app_commands.command(
    name="update_table",
    description="Update one row of the stats table (admin/editor only)"
)
@app_commands.describe(
    name="Entry name",
    sing="New sing value",
    dance="New dance value",
    rally="New rally value"
)
async def update_table(
    interaction: Interaction,
    name: str,
    sing: int,
    dance: int,
    rally: float = None
):
    user = interaction.user

    # Permission check
    if not (is_admin(user) or is_editor(user.id)):
        return await interaction.response.send_message(
            "❌ You don’t have permission to update stats.",
            ephemeral=True
        )

    # Defer
    await interaction.response.defer(thinking=True)

    # Choose client
    client = admin_supabase

    # Build payload
    payload = {k: v for k, v in {"sing": sing, "dance": dance, "rally": rally}.items() if v is not None}
    if not payload:
        return await interaction.followup.send("❌ Nothing to update.")

    # Execute
    try:
        res = client.table("stats").update(payload).eq("name", name).execute()
        data = res.data or []
    except Exception as exc:
        logger.error("Failed to update stats for %s: %s", name, exc, exc_info=True)
        return await interaction.followup.send(
            "❌ Could not update row. Please try again later."
        )

    if not data:
        return await interaction.followup.send(f"❌ No entry found for `{name}`")

    feedback = " ".join(f"{k}={v}" for k, v in payload.items())
    await interaction.followup.send(f"✅ Updated `{name}` with {feedback}")


def setup(bot: commands.Bot):
    bot.tree.add_command(update_table)
