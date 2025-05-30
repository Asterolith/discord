#_ commands/manage_editor.py
import discord
from datetime import datetime
from discord import app_commands
from discord.ext import commands
from py.helpers import is_admin, admin_supabase


@app_commands.command(
    name="view_editors",
    description="List all current editors (admin only)"
)
async def view_editors(interaction: discord.Interaction):
    # 1) Authorization
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ You’re not authorized.", ephemeral=True)
        return

    # 2) Defer before the DB hit
    await interaction.response.defer(thinking=True)

    # 3) Fetch all rows (no .order() here)
    try:
        res = admin_supabase.table("stats_editors_rights") \
                           .select("discord_id, discord_name, added_at") \
                           .execute()
        rows = res.data or []
    except Exception as e:
        return await interaction.followup.send(f"❌ Failed to fetch editors: {e}", ephemeral=True)

    # 4) Sort descending by ‘added_at’ in Python
    try:
        rows.sort(key=lambda r: r["added_at"], reverse=True)
    except KeyError:
        # if added_at missing, just leave as-is
        pass

    if not rows:
        return await interaction.followup.send("ℹ️ No editors found.", ephemeral=True)

    # 5) Build a monospace table
    header = "ID               | Name | Added At (UTC)"
    sep    = "-" * len(header)
    lines  = [header, sep]

    for r in rows:
        ts = datetime.fromisoformat(r['added_at']).strftime("%Y-%m-%d %H:%M")
        lines.append(
            f"{r['discord_id']:<16} | {r['discord_name']:<32} | {ts}"
        )

    table = "```" + "\n".join(lines) + "```"

    # 6) Send it
    await interaction.followup.send(table, ephemeral=True)


# — add_editor — Admin only
@app_commands.command(
    name="add_editor",
    description="Grant someone editor rights (admin only)"
)
async def add_editor(interaction: discord.Interaction, member: discord.Member):
    if not is_admin(interaction.user):
        return await interaction.response.send_message("❌NOT authorized.", ephemeral=True)
    await interaction.response.defer(thinking=True)
    
    try:
        # capture name + discriminator + timestamp
        payload = {
            "discord_id": member.id,
            "discord_name": member.name,
            # "added_at" uses default NOW() in Postgres if not specified
        }
        res = admin_supabase.table("stats_editors_rights")\
                            .insert(payload)\
                            .execute()
        # if the insert returns no data, it failed
        if not res.data:
            raise RuntimeError("Insert failed")
    except Exception as e:
        return await interaction.followup.send(f"❌ Failed to add editor: {e}")
    
    await interaction.followup.send(f"✅ {member.mention} can now view & update stats.", ephemeral=True)


# — remove_editor — Admin only
@app_commands.command(
    name="remove_editor",
    description="Revoke editor rights (admin only)"
)
async def remove_editor(interaction: discord.Interaction, member: discord.Member):
    if not is_admin(interaction.user):
        return await interaction.response.send_message("❌NOT authorized.", ephemeral=True)
    await interaction.response.defer(thinking=True)
    
    try:
        res = admin_supabase.table("stats_editors_rights") \
                            .delete() \
                            .eq("discord_id", member.id) \
                            .execute()
    # PostgREST returns an empty list if nothing was deleted
        if not res.data:
            return await interaction.followup.send(
                f"❌ {member.mention} was not an editor.", ephemeral=True
            )
    except Exception as e:
        return await interaction.followup.send(
            f"❌ Failed to remove editor: {e}", ephemeral=True
        )

    await interaction.followup.send(f"✅ {member.mention} can no longer view & update stats.", ephemeral=True)


def setup(bot: commands.Bot):
    bot.tree.add_command(view_editors)
    bot.tree.add_command(add_editor)
    bot.tree.add_command(remove_editor)