# py/paginator.py
import discord
from discord import  ui
from py.helpers import format_header, format_row, blank_row, sort_data, ROWS_PER_PAGE

class TablePaginator(ui.View):
    def __init__(self, data, sort_by: str, sort_desc: bool, page: int):
        super().__init__(timeout=120)
        self.data = data
        self.sort_by = sort_by
        self.sort_desc = sort_desc
        self.page = page
        self.update_buttons()

    def update_buttons(self):
        max_pages = max(1, (len(self.data) - 1) // ROWS_PER_PAGE + 1)
        self.prev_button.disabled = self.page <= 1
        self.next_button.disabled = self.page >= max_pages


    @ui.button(label='◀ Prev', style=discord.ButtonStyle.primary, custom_id='prev')
    async def prev_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.change_page(interaction, self.page - 1)


    @ui.button(label='Next ▶', style=discord.ButtonStyle.primary, custom_id='next')
    async def next_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.change_page(interaction, self.page + 1)


    async def change_page(self, interaction: discord.Interaction, new_page: int):
        self.page = new_page
        # re-sort
        data = sort_data(self.data, self.sort_by, self.sort_desc) if self.sort_by else self.data
        # paginate
        start = (self.page - 1) * ROWS_PER_PAGE
        page_data = data[start:start + ROWS_PER_PAGE]
        # re-render
        lines = [format_header(), '-' * len(format_header())]
        for row in page_data:
            lines.append(format_row(row))
            lines.append(blank_row())
            
        block = '```css\n' + '\n'.join(lines) + '\n```'
        self.update_buttons()

         # Attempt to edit via interaction.response
        try:
            await interaction.response.edit_message(content=block, view=self)
        except discord.errors.NotFound:
            # fallback to followup if response not available
            await interaction.followup.edit_message(message_id=interaction.message.id, content=block, view=self)