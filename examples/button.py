"""A simple example on the use of buttons with disnake-ext-components."""

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


# Then we make a simple component and register it to the manager.
@manager.register
class MyButton(components.RichButton):
    label: typing.Optional[str] = "0"  # Set the label of the button...

    count: int  # Define a custom_id parameter...

    async def callback(self, interaction: components.MessageInteraction) -> None:
        self.count += 1  # Increment count...
        self.label = str(self.count)  # update label to count...

        await interaction.response.edit_message(components=self)  # ...and update it!


# Finally, we make a command that sends the component.
@bot.slash_command()  # pyright: ignore  # still some unknowns in disnake
async def test_button(inter: disnake.CommandInteraction) -> None:
    # Wrapping the interaction allows you to send the component as-is.
    wrapped = components.wrap_interaction(inter)
    component = MyButton(count=0)

    await wrapped.response.send_message(components=component)

    # If we had not wrapped the interaction, we would have needed to do
    # `await inter.send(components=await component.as_ui_component())`
    # instead.


# Lastly, we run the bot.
bot.run(os.getenv("EXAMPLE_TOKEN"))
