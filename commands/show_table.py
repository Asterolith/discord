

import discord
from discord import app_commands
from discord.ext import commands
from ..py.helpers import (
    is_admin, load_data, user_client_for, admin_supabase,
    ROWS_PER_PAGE, HEADER, SEP,
    format_row, blank_row, sort_data
)
from ..py.paginator import TablePaginator


# /show_table: pagination & sort for stats
@app_commands.command(name="show_table", description="Show table with sort & pagination (editor)")
@app_commands.describe(
    sort_by='name | sing | dance | rally',
    sort_desc='Descending order? (default True)',
    page='Page number (default 1)'
)
async def show_table(interaction: discord.Interaction,
                     sort_by: str = None,
                     sort_desc: bool = True,
                     page: int = 1):
    # Try to defer, but if it’s “unknown,” ignore it
    try:
        await interaction.response.defer(thinking=True)
    except discord.errors.NotFound:
        pass

    # 2) Validate
    sort_by = sort_by.lower() if sort_by else None
    if sort_by and sort_by not in ('name','sing','dance','rally'):
        return await interaction.followup.send('❌ Invalid sort column')

    # 3) admin or editor
    client = admin_supabase if is_admin(interaction.user) else user_client_for(interaction.user.id)
    rows = client.table('stats').select('*').execute().data or []
    if sort_by:
        rows = sort_data(rows, sort_by, sort_desc)

    # 4) Slice page
    start = (page-1)*ROWS_PER_PAGE
    page_data = rows[start:start+ROWS_PER_PAGE]
    if not page_data:
        return await interaction.followup.send('❌ Page out of range')

    # 5) Build text block
    lines = [HEADER, SEP]
    for r in page_data:
        lines.append(format_row(r)); 
        lines.append(blank_row())
    block = f"```css\n{chr(10).join(lines)}\n```"

    # 6) Build paginator view with the full list, so it knows max pages
    view = TablePaginator(rows, sort_by, sort_desc, page)

    try:
        await interaction.response.edit_message(content=block, view=view)
    except discord.errors.NotFound:
        # fallback to editing the original followup
        await interaction.followup.edit_message(
        message_id=interaction.message.id,
        content=block,
        view=view
        )

# register
def setup(bot: commands.Bot):
    bot.tree.add_command(show_table)