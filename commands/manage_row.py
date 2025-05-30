
import discord
from discord import app_commands
from discord.ext import commands
from ..py.helpers import is_admin, admin_supabase


@app_commands.command(name="add_row", description="Add a new row (admin)")
async def add_row(interaction: discord.Interaction,
                  name: str,
                  sing: int,
                  dance: int,
                  rally: float):
    if not is_admin(interaction.user):
        return await interaction.response.send_message("❌NOT authorized.")
    await interaction.response.defer(thinking=True)

    try:
        res = admin_supabase.table("stats")\
                            .insert({"name": name, "sing": sing, "dance": dance, "rally": rally})\
                            .execute()
    except Exception as e:
        return await interaction.followup.send(f"❌ Insert failed: {e}")

    if not (res.data and len(res.data) > 0):
        return await interaction.followup.send("❌ Insert returned no data!")

    await interaction.followup.send(f"✅ Row for `{name}` added.")


# — delete_row —
@app_commands.command(name="delete_row", description="Delete a row (admin)")
async def delete_row(interaction: discord.Interaction, name: str):
    if not is_admin(interaction.user):
        return await interaction.response.send_message("❌NOT authorized.")
    await interaction.response.defer(thinking=True)

    try:
        res = admin_supabase.table("stats")\
                    .delete()\
                    .eq("name", name)\
                    .execute()
    except Exception as e:
        return await interaction.followup.send(f"❌ Delete failed: {e}")

    if not (res.data and len(res.data) > 0):
        return await interaction.followup.send(f"❌ No row found for `{name}` to delete.")
    
    await interaction.followup.send(f"🗑️ Row for `{name}` deleted.")


def setup(bot: commands.Bot):
    bot.tree.add_command(add_row)
    bot.tree.add_command(delete_row)