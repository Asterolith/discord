#_ commands/show_table.py
from discord import app_commands, Interaction, errors
from discord.ext import commands
from py.helpers import (
    is_admin, is_editor, user_client_for, admin_supabase,
    ROWS_PER_PAGE, HEADER, SEP,
    SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY, JWT_SECRET, #import for DEBUG
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
    # ── 1) Permission check ────────────────────────────────────────────────────
    if not (is_admin(interaction.user) or is_editor(interaction.user.id)):
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
    client = admin_supabase if is_admin(interaction.user) else user_client_for(interaction.user.id)

    # 2) DEBUG: print out the headers your client will send
    try:
        session = client._session  # httpx.Session under the hood
        headers = dict(session.headers)
    except Exception:
        headers = "<couldn't fetch headers>"
    print(f"[DEBUG show_table] using {'ADMIN' if is_admin(interaction.user) else 'USER'} client")
    print("  SUPABASE_URL:", client._url)
    print("  Authorization header:", headers.get("Authorization"))
    print("[DEBUG] Supabase headers:", client._session.headers)

    # 3) If using a user‐scoped client, also show the first/last bits of the JWT
    if not is_admin(interaction.user):
        token = headers.get("Authorization", "").split("Bearer ")[-1]
        print(f"  user JWT (first/last 8 chars): {token[:8]}…{token[-8:]}")

    # 4) Now attempt the actual query, but catch the raw response
    try:
        rows = client.table("stats").select("*").execute().data or []
    except Exception as e:
        # dump the raw HTTP text if possible
        try:
            resp = e.args[0]  # the PostgREST APIError dict
            print("[DEBUG show_table] raw error payload:", resp)
        except:
            pass
        await interaction.followup.send("❌ Could not fetch data from Supabase. Check the logs for details.")
        return
    

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