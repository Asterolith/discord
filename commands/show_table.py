#_ commands/show_table.py
from discord import app_commands, Interaction, errors
from discord.ext import commands
from py.helpers import (
    is_admin, is_editor, user_client_for, admin_supabase,
    ROWS_PER_PAGE, HEADER, SEP,
    sort_data, format_row, blank_row
)
from py.log_config import safe_select
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
async def show_table(
    interaction: Interaction,
    sort_by: str = None,
    sort_desc: bool = True,
    page: int = 1
):
    user = interaction.user

    # ── 1) Permission check ────────────────────────────────────────────────────
    if not (is_admin(user) or is_editor(user.id)):
        return await interaction.response.send_message(
            "❌ You don’t have permission to view stats.",
            ephemeral=True
        )

    # ── 2) Defer reply ─────────────────────────────────────────────────────────
    try:
        await interaction.response.defer(thinking=True)
    except errors.NotFound:
        # if already acknowledged, ignore
        pass

    # ── 3) Fetch all rows under correct client ────────────────────────────────
    client = admin_supabase if is_admin(user) else user_client_for(user.id)
    
    print("[DEBUG] Supabase headers:", client._session.headers)

    try:
        rows = safe_select(client, "stats", "*")
    except Exception:
        return await interaction.followup.send(
            "❌ Could not fetch data from Supabase. Check the logs for details.",
            ephemeral=True
        )


    # ── 4) Validate sort column ───────────────────────────────────────────────
    sort_by = sort_by.lower() if sort_by else None
    if sort_by and sort_by not in ("name", "sing", "dance", "rally"):
        return await interaction.followup.send("❌ Invalid sort column")

    # ── 5) Sort & paginate in Python ──────────────────────────────────────────
    if sort_by:
        rows = sort_data(rows, sort_by, sort_desc)
    start = (page - 1) * ROWS_PER_PAGE
    page_data = rows[start : start + ROWS_PER_PAGE]
    if not page_data:
        return await interaction.followup.send("❌ Page out of range")

    # ── 6) Build code block ───────────────────────────────────────────────────
    lines = [HEADER, SEP]
    for r in page_data:
        lines.append(format_row(r))
        lines.append(blank_row())
    block = f"```css\n{chr(10).join(lines)}\n```"

    # ── 7) Instantiate paginator view ────────────────────────────────────────
    view = TablePaginator(rows, sort_by, sort_desc, page)

    # ── 8) Send once ──────────────────────────────────────────────────────────
    await interaction.followup.send(content=block, view=view)


def setup(bot: commands.Bot):
    bot.tree.add_command(show_table)