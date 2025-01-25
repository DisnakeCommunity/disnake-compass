"""A simple example on the use of buttons with disnake-ext-components."""

import os
import typing

import disnake
from disnake.ext import commands, components

bot = commands.InteractionBot()

manager = components.get_manager()
manager.add_to_bot(bot)


@manager.register
class MyButton(components.RichButton):
    label: typing.Optional[str] = "0"

    count: int = 0

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        self.count += 1
        self.label = str(self.count)

        component = await self.as_ui_component()
        await interaction.response.edit_message(components=component)


@bot.slash_command()  # pyright: ignore  # still some unknowns in disnake
async def test_button(interaction: disnake.CommandInteraction) -> None:
    component = await MyButton().as_ui_component()
    await interaction.response.send_message(components=component)


bot.run(os.getenv("EXAMPLE_TOKEN"))
