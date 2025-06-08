# commands/manage_editor.py

from datetime import datetime
from discord import app_commands, Interaction, Member, errors
from discord.ext import commands

from py.helpers import is_admin, admin_supabase
from py.log_config import logger

# ─── view_editors ────────────────────────────────────────────────────────────────
@app_commands.command(
    name="view_editors",
    description="List all current editors (admin only)"
)
async def view_editors(interaction: Interaction):
    # 1) Authorization
    user = interaction.user
    if not is_admin(user):
        return await interaction.response.send_message(
            "❌ You’re not authorized.",
            ephemeral=True
        )

    # 2) Defer (ephemeral)
    try:
        await interaction.response.defer(thinking=True, ephemeral=True)
    except errors.InteractionResponded:
        pass

    # 3) Fetch & sort
    try:
        res = admin_supabase.table("stats_editors_rights") \
                           .select("discord_id, discord_name, added_at") \
                           .execute()
        rows = res.data or []
        rows.sort(key=lambda r: r["added_at"], reverse=True)
    except Exception as exc:
        logger.error("Error fetching editors list: %s", exc, exc_info=True)
        return await interaction.followup.send(
            "❌ Failed to fetch editors. Please try again later.",
            ephemeral=True
        )

    # 4) No editors?
    if not rows:
        return await interaction.followup.send(
            "ℹ️ No editors found.",
            ephemeral=True
        )

    # 5) Build table
    header = "Discord ID       | Username            | Added At (UTC)"
    sep    = "-" * len(header)
    lines  = [header, sep]
    for r in rows:
        ts = datetime.fromisoformat(r["added_at"]).strftime("%Y-%m-%d %H:%M")
        lines.append(f"{r['discord_id']:<17} | {r['discord_name']:<18} | {ts}")

    table = "```" + "\n".join(lines) + "```"

    # 6) Send
    await interaction.followup.send(table, ephemeral=True)


# ─── add_editor ─────────────────────────────────────────────────────────────────
@app_commands.command(
    name="add_editor",
    description="Grant someone editor rights (admin only)"
)
async def add_editor(interaction: Interaction, member: Member):
    # 1) Authorization
    user = interaction.user
    if not is_admin(user):
        return await interaction.response.send_message(
            "❌ You’re not authorized.",
            ephemeral=True
        )

    # 2) Defer
    try:
        await interaction.response.defer(thinking=True, ephemeral=True)
    except errors.InteractionResponded:
        pass

    # 3) Insert
    try:
        res = admin_supabase.table("stats_editors_rights") \
                            .insert({
                                "discord_id": member.id,
                                "discord_name": member.name
                            }).execute()
        if not res.data:
            raise RuntimeError("No rows inserted")
    except Exception as exc:
        logger.error("Error adding editor %s: %s", member.id, exc, exc_info=True)
        return await interaction.followup.send(
            f"❌ Failed to add {member.mention} as editor.",
            ephemeral=True
        )

    # 4) Confirm
    await interaction.followup.send(
        f"✅ {member.mention} is now an editor.",
        ephemeral=True
    )


# ─── remove_editor ───────────────────────────────────────────────────────────────
@app_commands.command(
    name="remove_editor",
    description="Revoke editor rights (admin only)"
)
async def remove_editor(interaction: Interaction, member: Member):
    # 1) Authorization
    user = interaction.user
    if not is_admin(user):
        return await interaction.response.send_message(
            "❌ You’re not authorized.",
            ephemeral=True
        )

    # 2) Defer
    try:
        await interaction.response.defer(thinking=True, ephemeral=True)
    except errors.InteractionResponded:
        pass

    # 3) Delete
    try:
        res = admin_supabase.table("stats_editors_rights") \
                            .delete() \
                            .eq("discord_id", member.id) \
                            .execute()
        if not res.data:
            return await interaction.followup.send(
                f"❌ {member.mention} was not an editor.",
                ephemeral=True
            )
    except Exception as exc:
        logger.error("Error removing editor %s: %s", member.id, exc, exc_info=True)
        return await interaction.followup.send(
            f"❌ Failed to remove {member.mention}.",
            ephemeral=True
        )

    # 4) Confirm
    await interaction.followup.send(
        f"✅ {member.mention} is no longer an editor.",
        ephemeral=True
    )


# ─── Registration ────────────────────────────────────────────────────────────────
def setup(bot: commands.Bot):
    for cmd in (view_editors, add_editor, remove_editor):
        bot.tree.add_command(cmd)