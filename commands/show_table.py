#_ commands/show_table.py
from discord import app_commands, Interaction, errors
from discord.ext import commands
from py.helpers import (
    is_admin, user_client_for, admin_supabase,
    ROWS_PER_PAGE, HEADER, SEP,
    sort_data, format_row, blank_row
)
from py.paginator import TablePaginator


# /show_table: pagination & sort for stats
@app_commands.command(
        name="show_table", 
        description="Show table with sort & pagination (editor)")
@app_commands.describe(
    sort_by='name | sing | dance | rally',
    sort_desc='Descending order? (default True)',
    page='Page number (default 1)'
)
async def show_table(interaction: Interaction,
                     sort_by: str = None,
                     sort_desc: bool = True,
                     page: int = 1):
    # 1) Defer this registers follow up later, but if it’s “unknown,” ignore it
    try:
        await interaction.response.defer(thinking=True)
    except errors.NotFound:
        pass

    # 2) Validate and fetch all rows
    sort_by = sort_by.lower() if sort_by else None
    if sort_by and sort_by not in ('name','sing','dance','rally'):
        return await interaction.followup.send('❌ Invalid sort column')

    client = admin_supabase if is_admin(interaction.user) else user_client_for(interaction.user.id)
    rows = client.table('stats').select('*').execute().data or []

    # 3) Apply sort & pagination in Python
    if sort_by:
        rows = sort_data(rows, sort_by, sort_desc)

    start = (page-1) * ROWS_PER_PAGE
    page_data = rows[start:start+ROWS_PER_PAGE]
    if not page_data:
        return await interaction.followup.send('❌ Page out of range')

    # 4) Build text block
    lines = [HEADER, SEP]
    for r in page_data:
        lines.append(format_row(r)); 
        lines.append(blank_row())
    block = f"```css\n{chr(10).join(lines)}\n```"

    # 5) Build paginator view with the full list, so it knows max pages
    view = TablePaginator(rows, sort_by, sort_desc, page)

    # 6) Finally, send via followup (only once!)
    await interaction.followup.send(content=block, view=view)
    

# register
def setup(bot):
    bot.tree.add_command(show_table)