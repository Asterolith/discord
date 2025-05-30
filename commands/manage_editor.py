#_ commands/manage_editor.py
from datetime import datetime
import discord
from discord import app_commands, Interaction, Member
from discord.ext import commands
from py.helpers import is_admin, admin_supabase


@app_commands.command(
    name="view_editors",
    description="List all current editors (admin only)"
)
async def view_editors(interaction: Interaction):
    if not is_admin(interaction.user):
        return await interaction.response.send_message("❌ You’re not authorized.", ephemeral=True)

    # defer but ignore if already responded
    try:
        await interaction.response.defer(thinking=True, ephemeral=True)
    except discord.errors.InteractionResponded:
        pass

    # fetch & sort
    try:
        res = admin_supabase.table("stats_editors_rights") \
                           .select("discord_id, discord_name, added_at") \
                           .execute()
        rows = res.data or []
        rows.sort(key=lambda r: r["added_at"], reverse=True)
    except Exception as e:
        return await interaction.followup.send(f"❌ Failed to fetch editors: {e}", ephemeral=True)

    if not rows:
        return await interaction.followup.send("ℹ️ No editors found.", ephemeral=True)

    header = "ID               | Name               | Added At (UTC)"
    sep = "-" * len(header)
    lines = [header, sep]
    for r in rows:
        ts = datetime.fromisoformat(r["added_at"]).strftime("%Y-%m-%d %H:%M")
        lines.append(f"{r['discord_id']:<16} | {r['discord_name']:<18} | {ts}")
    table = "```" + "\n".join(lines) + "```"

    await interaction.followup.send(table, ephemeral=True)


@app_commands.command(
    name="add_editor",
    description="Grant someone editor rights (admin only)"
)
async def add_editor(interaction: Interaction, member: Member):
    if not is_admin(interaction.user):
        return await interaction.response.send_message("❌ You’re not authorized.", ephemeral=True)
    try:
        await interaction.response.defer(thinking=True, ephemeral=True)
    except discord.errors.InteractionResponded:
        pass

    try:
        res = admin_supabase.table("stats_editors_rights") \
                            .insert({
                                "discord_id": member.id,
                                "discord_name": member.name
                            }).execute()
        if not res.data:
            raise RuntimeError("No rows inserted")
    except Exception as e:
        return await interaction.followup.send(f"❌ Failed to add editor: {e}", ephemeral=True)

    await interaction.followup.send(f"✅ {member.mention} can now view & update stats.", ephemeral=True)


@app_commands.command(
    name="remove_editor",
    description="Revoke editor rights (admin only)"
)
async def remove_editor(interaction: Interaction, member: Member):
    if not is_admin(interaction.user):
        return await interaction.response.send_message("❌ You’re not authorized.", ephemeral=True)
    try:
        await interaction.response.defer(thinking=True, ephemeral=True)
    except discord.errors.InteractionResponded:
        pass

    try:
        res = admin_supabase.table("stats_editors_rights") \
                            .delete() \
                            .eq("discord_id", member.id) \
                            .execute()
        if not res.data:
            return await interaction.followup.send(f"❌ {member.mention} was not an editor.", ephemeral=True)
    except Exception as e:
        return await interaction.followup.send(f"❌ Failed to remove editor: {e}", ephemeral=True)

    await interaction.followup.send(f"✅ {member.mention} can no longer view & update stats.", ephemeral=True)


def setup(bot: commands.Bot):
    for cmd in (view_editors, add_editor, remove_editor):
        bot.tree.add_command(cmd)