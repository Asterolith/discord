import discord
from discord.ext import commands
from discord import app_commands, ui
from table_bot import *

class TablePaginator(discord.ui.View):
    def __init__(self, data, sort_by, sort_desc, page, **kwargs):
        super().__init__(**kwargs, timeout=120)         #_2min timeout
        self.data = data

        #_Disable preview on page 1
        self.prev.disabled = (page <=1)
        #_Disable Next when no more pages:
        max_pages = (len(data) -1)// ROWS_PER_PAGE + 1
        self.next.disabled = (page >= max_pages)

    @ui.button(label="◀ Prev", style=discord.ButtonStyle.blurple)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_page(interaction, self.page - 1)

    @ui.button(label="Next ▶", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_page(interaction, self.page + 1)

    async def change_page(self, interaction, new_page):
        self.page = new_page
        #_resort & paginate
        data = sort_data(self.data, self.sort_by, self.sort_desc) if self.sort_by else self.data
        start = (self.page - 1) * ROWS_PER_PAGE
        page_data = data[start:start + ROWS_PER_PAGE]
        #_reformat
        lines = [format_header(), '_'*len(format_header())]
        for row in page_data:
            lines.append(format_row(row))
            lines.append('_'*len(format_row(row)))
        block = "'''css\n" + "\n".join(lines) + "\n'''"
        #_update button state
        self.prev.disabled = (self.page <=1)
        max_pages = (len(data) -1)// ROWS_PER_PAGE + 1
        self.next.disabled = (self.page >= max_pages)
        await interaction.response.edit_message(content=block, view=self)
