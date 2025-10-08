"""An example of having multiple disnake-compass components interact."""

import os
import typing

import disnake
from disnake.ext import commands

import disnake_compass

DEFAULT_OPTION = disnake.SelectOption(
    label="Please enable some options.",
    value="placeholder",
    default=True,
)

bot = commands.InteractionBot()

manager = disnake_compass.get_manager()
manager.add_to_client(bot)


@manager.register()
class OptionsToggleButton(disnake_compass.RichButton):
    """A button component that enables/disables options on a DynamicSelectMenu."""

    style: disnake.ButtonStyle = disnake.ButtonStyle.red
    options: typing.Sequence[str]

    def parse_options(self) -> typing.Sequence[disnake.SelectOption]:
        if self.style == disnake.ButtonStyle.red:
            return []

        return [disnake.SelectOption(label=option) for option in self.options]

    def update_select(self, components: typing.Sequence[disnake_compass.api.RichComponent]):
        select: DynamicSelectMenu | None = None
        options: list[disnake.SelectOption] = []

        for component in components:
            if isinstance(component, DynamicSelectMenu):
                if select is not None:
                    raise RuntimeError("Found more than one DynamicSelectMenu.")

                select = component

            elif isinstance(component, OptionsToggleButton):
                options.extend(component.parse_options())

        if not select:
            raise RuntimeError("Could not find a DynamicSelectMenu.")

        select.set_options(options)

    async def callback(self, interaction: disnake.MessageInteraction[disnake.Client]):
        # Get all components on the message for easier re-sending.
        # Both of these lists will automagically contain self so that any
        # changes immediately reflect without extra effort.
        layout, components = await manager.parse_message_components(interaction.message.components)

        # Toggle style for the clicked button.
        self.style = (
            disnake.ButtonStyle.red
            if self.style == disnake.ButtonStyle.green
            else disnake.ButtonStyle.green
        )

        # Add/remove options to the DynamicSelect based on whether this
        # button was toggled on or off.
        self.update_select(components)

        # Re-send and update all components.
        await manager.update_layout(layout, components)
        await interaction.response.edit_message(components=layout)


@manager.register()
class DynamicSelectMenu(disnake_compass.RichStringSelect):
    """A select menu that has its options externally managed."""

    def __attrs_post_init__(self) -> None:  # See the `attrs.py` example.
        self.set_options([])

    def set_options(self, options: typing.List[disnake.SelectOption]):
        if options:
            self.options = options
            self.max_values = len(options)
            self.disabled = False

        else:
            self.options = [DEFAULT_OPTION]
            self.max_values = 1
            self.disabled = True

    async def callback(self, interaction: disnake.MessageInteraction[disnake.Client]) -> None:
        selection = (
            "\n".join(f"- {value}" for value in interaction.values)
            if interaction.values
            else "nothing :("
        )

        await interaction.response.send_message(f"You selected:\n{selection}")


@bot.slash_command()
async def test_components(
    interaction: disnake.CommandInteraction[disnake.Client],
) -> None:
    # TODO: Maybe a utility method to turn a sequence of rich components into a
    #       sequence of UI components?
    layout = [
        [
            await OptionsToggleButton(
                label="numbers", options=["1", "2", "3", "4", "5"]
            ).as_ui_component(),
            await OptionsToggleButton(
                label="letters", options=["a", "b", "c", "d", "e"]
            ).as_ui_component(),
            await OptionsToggleButton(
                label="symbols", options=["*", "&", "#", "+", "-"]
            ).as_ui_component(),
        ],
        [await DynamicSelectMenu().as_ui_component()],
    ]

    await interaction.response.send_message(components=layout)


bot.run(os.environ["EXAMPLE_TOKEN"])
