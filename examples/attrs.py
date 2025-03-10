"""An example showcasing how attrs utilities can be used with disnake-compass."""

import os

import disnake
import disnake_compass
from disnake.ext import commands

bot = commands.InteractionBot()

manager = disnake_compass.get_manager()
manager.add_to_client(bot)


@manager.register
class CustomisableSelect(disnake_compass.RichStringSelect):
    def __attrs_post_init__(self) -> None:
        self.max_values = len(self.options)

    async def callback(
        self, interaction: disnake.MessageInteraction[disnake.Client]
    ) -> None:
        selection = (
            "\n".join(f"- {value}" for value in interaction.values)
            if interaction.values
            else "nothing :("
        )

        await interaction.response.send_message(
            f"You selected:\n{selection}",
            ephemeral=True,
        )


@bot.slash_command()
async def make_select(
    interaction: disnake.CommandInteraction[disnake.Client], options: str
) -> None:
    if not options.strip():
        await interaction.response.send_message("You must specify at least one option!")
        return

    actual_options = [
        disnake.SelectOption(label=option.strip())
        for option in options.split(",")
    ]  # fmt: skip

    if len(actual_options) > 25:
        await interaction.response.send_message("You must specify at most 25 options!")
        return

    component = await CustomisableSelect(options=actual_options).as_ui_component()
    await interaction.response.send_message(
        components=component,
    )


bot.run(os.getenv("EXAMPLE_TOKEN"))
