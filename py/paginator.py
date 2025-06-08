# py/paginator.py
import discord
from discord import ui
from py.helpers import HEADER, format_row, blank_row, sort_data, ROWS_PER_PAGE

class TablePaginator(ui.View):
    def __init__(
        self,
        data: list[dict],
        sort_by: str | None = None,
        sort_desc: bool = False,
        page: int = 1
    ):
        super().__init__(timeout=120)
        self.data = data
        self.sort_by = sort_by
        self.sort_desc = sort_desc
        self.page = page

        # Pre-render header and separator once
        self.header = HEADER
        self.sep = '-' * len(self.header)

        self._update_button_states()

    def _update_button_states(self) -> None:
        # Compute total pages and enable/disable buttons
        total = max(1, (len(self.data) - 1) // ROWS_PER_PAGE + 1)
        self.prev_button.disabled = self.page <= 1
        self.next_button.disabled = self.page >= total


    @ui.button(label='◀ Prev', style=discord.ButtonStyle.primary, custom_id='table_prev')
    async def prev_button(self, interaction: discord.Interaction, button: ui.Button) -> None:
        await self._change_page(interaction, self.page - 1)

    @ui.button(label='Next ▶', style=discord.ButtonStyle.primary, custom_id='table_next')
    async def next_button(self, interaction: discord.Interaction, button: ui.Button) -> None:
        await self._change_page(interaction, self.page + 1)

    async def _change_page(self, interaction: discord.Interaction, new_page: int) -> None:
        """
        Update the current page, re-render the table, and edit the message.
        """
        self.page = new_page
        # Apply sorting if requested
        rows = sort_data(self.data, self.sort_by, self.sort_desc) if self.sort_by else self.data
        # Paginate
        start = (self.page - 1) * ROWS_PER_PAGE
        page_rows = rows[start:start + ROWS_PER_PAGE]
        
        # Render table text
        lines = [self.header, self.sep]
        for r in page_rows:
            lines.append(format_row(r))
            lines.append(blank_row())
        
        text = "\n".join(lines)
        block = f"```css\n{text}\n```"
            
        # block = '```css\n' + '\n'.join(lines) + '\n```'
       
        # Update navigation buttons
        self._update_button_states()

        # Try to edit interaction, fallback to followup
        try:
            await interaction.response.edit_message(content=block, view=self)
        except discord.errors.NotFound:
            await interaction.followup.edit_message(
                message_id=interaction.message.id,
                content=block,
                view=self
            )