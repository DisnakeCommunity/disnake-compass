"""An example showcasing how attrs utilities can be used with ext-components."""

import os

import disnake
from disnake.ext import commands, components

bot = commands.InteractionBot()

manager = components.get_manager()
manager.add_to_bot(bot)


@manager.register
class CustomisableSelect(components.RichStringSelect):
    def __attrs_post_init__(self) -> None:
        self.max_values = len(self.options)

    async def callback(self, interaction: components.MessageInteraction) -> None:
        selection = (
            "\n".join(f"- {value}" for value in interaction.values)
            if interaction.values
            else "nothing :("
        )

        await interaction.response.send_message(
            f"You selected:\n{selection}", ephemeral=True
        )


@bot.slash_command()  # pyright: ignore
async def make_select(interaction: disnake.CommandInteraction, options: str) -> None:
    """Make your own select menu.

    Parameters
    ----------
    options:
        A comma-separated string with all options. Max 25.

    """
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

    wrapped = components.wrap_interaction(interaction)
    await wrapped.response.send_message(
        components=CustomisableSelect(options=actual_options),
    )


bot.run(os.getenv("EXAMPLE_TOKEN"))
