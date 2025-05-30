
import discord
from discord import app_commands
from discord.ext import commands
from ..py.helpers import is_admin, admin_supabase, user_client_for

# — update_table —
@app_commands.command(name="update_table", description="Update a stats row (editor)")
@app_commands.describe(name='Entry name', sing='New sing value', dance='New dance value', rally='New rally value')
async def update_table(interaction: discord.Interaction,
                       name: str,
                       sing: int,
                       dance: int,
                       rally: float = None):
    await interaction.response.defer(thinking=True)

    if is_admin(interaction.user):
        client = admin_supabase    # uses your service_role key, bypasses RLS
    else:
        client = user_client_for(interaction.user.id)
    
    # Build update payload, dropping None
    payload = {k: v for k, v in {"sing": sing, "dance": dance, "rally": rally}.items() if v is not None}

    # update the row
    try:
        res = client.table("stats").update(payload).eq("name", name).execute()
    except Exception as e:
        return await interaction.followup.send(f"❌ Update failed: {e}")
    
    # if nothing changed, row didn't exist
    if not(res.data or len(res.data) > 0):
        return await interaction.followup.send(f"❌ No entry found for `{name}`")

    feedback = " ".join(f"{k}={v}" for k, v in payload.items())
    await interaction.followup.send(f"✅ Updated `{name}` with {feedback}")


def setup(bot: commands.Bot):
    bot.tree.add_command(update_table)