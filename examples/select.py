"""A simple example on the use of selects with disnake-ext-components.

For this example, we implement a select menu with double functionality.
Firstly, the select allows you to select one of three slots. After selecting a
slot, the select is modified to instead allow you to select a colour. The
selected slot and colour are then combined to colour the corresponding square.
"""

from __future__ import annotations

import os
import typing

import disnake
from disnake.ext import commands, components

# First and foremost, we create a bot as per usual. Since we don't need any
# prefix command capabilities, we opt for an InteractionBot.
bot = commands.InteractionBot()

# Next, we make a component manager and register it to the bot.
manager = components.get_manager()
manager.add_to_bot(bot)


# Define possible slots for our select.
LEFT = "\N{BLACK LEFT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}"
MIDDLE = "\N{BLACK CIRCLE FOR RECORD}\N{VARIATION SELECTOR-16}"
RIGHT = "\N{BLACK RIGHT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}"

SLOT_OPTIONS = [
    disnake.SelectOption(label="Left", value="left", emoji=LEFT),
    disnake.SelectOption(label="Middle", value="middle", emoji=MIDDLE),
    disnake.SelectOption(label="Right", value="right", emoji=RIGHT),
    disnake.SelectOption(label="Finalise", emoji="\N{WHITE HEAVY CHECK MARK}"),
]


# Define possible colours for our select.
BLACK_SQUARE = "\N{BLACK LARGE SQUARE}"
BLUE_SQUARE = "\N{LARGE BLUE SQUARE}"
BROWN_SQUARE = "\N{LARGE BROWN SQUARE}"
GREEN_SQUARE = "\N{LARGE GREEN SQUARE}"
PURPLE_SQUARE = "\N{LARGE PURPLE SQUARE}"
RED_SQUARE = "\N{LARGE RED SQUARE}"
WHITE_SQUARE = "\N{WHITE LARGE SQUARE}"
YELLOW_SQUARE = "\N{LARGE YELLOW SQUARE}"

COLOUR_OPTIONS = [
    disnake.SelectOption(label="Black", value=BLACK_SQUARE, emoji=BLACK_SQUARE),
    disnake.SelectOption(label="Blue", value=BLUE_SQUARE, emoji=BLUE_SQUARE),
    disnake.SelectOption(label="Brown", value=BROWN_SQUARE, emoji=BROWN_SQUARE),
    disnake.SelectOption(label="Green", value=GREEN_SQUARE, emoji=GREEN_SQUARE),
    disnake.SelectOption(label="Purple", value=PURPLE_SQUARE, emoji=PURPLE_SQUARE),
    disnake.SelectOption(label="Red", value=RED_SQUARE, emoji=RED_SQUARE),
    disnake.SelectOption(label="White", value=WHITE_SQUARE, emoji=WHITE_SQUARE),
    disnake.SelectOption(label="Yellow", value=YELLOW_SQUARE, emoji=YELLOW_SQUARE),
]


# Then, we make and register the select.
@manager.register
class MySelect(components.RichStringSelect):
    # Set the placeholder text...
    placeholder: typing.Optional[str] = "Please select a square."
    options: typing.List[disnake.SelectOption] = SLOT_OPTIONS  # Set the options...

    slot: str = "0"  # We store the slot the user is currently working with...
    state: str = "slot"  # We store whether they're picking a slot or a colour...
    colour_left: str = BLACK_SQUARE  # And we store the colours for the three slots...
    colour_middle: str = BLACK_SQUARE
    colour_right: str = BLACK_SQUARE

    async def callback(self, inter: components.MessageInteraction) -> None:
        # First we get the selected value.
        assert inter.values is not None  # This should never raise for a select.
        selected = inter.values[0]

        # If the selection was a slot, run slot selection logic.
        # To keep things tidy, we use a separate function for this.
        if self.state == "slot":
            self.handle_slots(selected)

        # Otherwise, run colour selection logic.
        else:
            self.handle_colours(selected)

        # Render the new colours and update the select.
        msg = self.render_colours()
        await inter.response.edit_message(msg, components=self)

    def handle_slots(self, selected: str) -> None:
        # In case the user wishes to finalize, disable the select.
        if selected == "Finalise":
            self.disabled = True
            self.placeholder = "Woo!"
            return

        # Update options and display.
        self.options = COLOUR_OPTIONS
        self.placeholder = f"Please select a colour for the {selected} square."

        # Set the slot to the user's selection and set state to colour.
        self.slot = selected
        self.state = "colour"

    def handle_colours(self, selected: str) -> None:
        # Update options.
        self.options = SLOT_OPTIONS

        # Set the corresponding colour attribute and set state to slot.
        setattr(self, f"colour_{self.slot}", selected)
        self.state = "slot"

    def render_colours(self) -> str:
        # Render our three squares.
        return f"{self.colour_left}{self.colour_middle}{self.colour_right}\n"


# Finally, we make a command that sends the component.
# In this command, we initialise the timeout for the component.
@bot.slash_command()  # pyright: ignore  # still some unknowns in disnake
async def test_select(inter: disnake.CommandInteraction) -> None:
    # Wrapping the interaction allows you to send the component as-is.
    wrapped = components.wrap_interaction(inter)

    component = MySelect()
    await wrapped.response.send_message(
        component.render_colours(), components=component
    )

    # If we had not wrapped the interaction, we would have needed to do
    # `await inter.send(components=await component.as_ui_component())`
    # instead.


# Lastly, we run the bot.
bot.run(os.getenv("EXAMPLE_TOKEN"))
