# commands/update_table.py
from discord import app_commands, Interaction
from discord.ext import commands
from py.helpers import is_admin, is_editor, admin_supabase, user_client_for
from py.log_config import logger, safe_update
from postgrest.exceptions import APIError

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

    # ── 1) Permission check ────────────────────────────────────────────────────
    if not (is_admin(user) or is_editor(user.id)):
        return await interaction.response.send_message(
            "❌ You don’t have permission to update stats.",
            ephemeral=True
        )

    # ── 2) Defer ────────────────────────────────────────────────────────────────
    await interaction.response.defer(thinking=True)

    # ── 3) Pick client ─────────────────────────────────────────────────────────
    client = admin_supabase if is_admin(user) else user_client_for(user.id)

    # ── 4) Build payload dropping None ────────────────────────────────────────
    payload = {
        k: v
        for k, v in {"sing": sing, "dance": dance, "rally": rally}.items()
        if v is not None
    }

    # ── 5) Execute update ─────────────────────────────────────────────────────
    try:
        data = safe_update(client, 'stats', payload, {"name": name})
    except APIError:
        return await interaction.followup.send(
            "❌ Could not update row. Check logs for details."
        )

    # ── 6) Check if anything changed ──────────────────────────────────────────
    if not data:
        return await interaction.followup.send(f"❌ No entry found for `{name}`")

    # ── 7) Acknowledge ─────────────────────────────────────────────────────────
    feedback = " ".join(f"{k}={v}" for k, v in payload.items())
    await interaction.followup.send(f"✅ Updated `{name}` with {feedback}")


def setup(bot: commands.Bot):
    bot.tree.add_command(update_table)