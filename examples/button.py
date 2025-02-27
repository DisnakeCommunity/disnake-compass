"""A simple example on the use of buttons with disnake-compass."""

import os

import disnake
import disnake_compass
from disnake.ext import commands

bot = commands.InteractionBot()

manager = disnake_compass.get_manager()
manager.add_to_client(bot)


@manager.register
class MyButton(disnake_compass.RichButton):
    label: str | None = "0"

    count: int = 0

    async def callback(
        self, interaction: disnake.MessageInteraction[disnake.Client]
    ) -> None:
        self.count += 1
        self.label = str(self.count)

        component = await self.as_ui_component()
        await interaction.response.edit_message(components=component)


@bot.slash_command()
async def test_button(interaction: disnake.CommandInteraction[disnake.Client]) -> None:
    component = await MyButton().as_ui_component()
    await interaction.response.send_message(components=component)


bot.run(os.getenv("EXAMPLE_TOKEN"))
