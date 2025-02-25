"""A simple example on the use of component managers with disnake-compass."""

import os

import disnake
import disnake_compass
from disnake.ext import commands

bot = commands.InteractionBot()

manager = disnake_compass.get_manager()
manager.add_to_bot(bot)

foo_manager = disnake_compass.get_manager("foo")
deeply_nested_manager = disnake_compass.get_manager("foo.bar.baz")


@foo_manager.register
class FooButton(disnake_compass.RichButton):
    label: str | None = "0"

    count: int

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        self.count += 1
        self.label = str(self.count)

        component = await self.as_ui_component()
        await interaction.response.edit_message(components=component)


@deeply_nested_manager.register
class FooBarBazButton(disnake_compass.RichButton):
    label: str | None = "0"

    count: int

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        self.count += 1
        self.label = str(self.count)

        component = await self.as_ui_component()
        await interaction.response.edit_message(components=component)


@manager.as_callback_wrapper
async def wrapper(
    manager: disnake_compass.ComponentManager,
    component: disnake_compass.api.RichComponent,
    interaction: disnake.Interaction,
):
    print(
        f"User {interaction.user.name!r} interacted with component {type(component).__name__!r}...",
    )

    yield

    print(
        f"User {interaction.user.name!r}s interaction with component"
        f" {type(component).__name__!r} was successful!",
    )


class InvalidUserError(Exception):
    def __init__(self, message: str, user: disnake.User | disnake.Member) -> None:
        super().__init__(message)
        self.message = message
        self.user = user


@deeply_nested_manager.as_callback_wrapper
async def check_wrapper(
    manager: disnake_compass.api.ComponentManager,
    component: disnake_compass.api.RichComponent,
    interaction: disnake.Interaction,
):
    if (
        isinstance(interaction, disnake.MessageInteraction)
        and interaction.message.interaction
        and interaction.user != interaction.message.interaction.user
    ):
        message = "You are not allowed to use this component."
        raise InvalidUserError(message, interaction.user)

    yield


@deeply_nested_manager.as_exception_handler
async def error_handler(
    manager: disnake_compass.ComponentManager,
    component: disnake_compass.api.RichComponent,
    interaction: disnake.Interaction,
    exception: Exception,
):
    if isinstance(exception, InvalidUserError):
        message = f"{exception.user.mention}, {exception.message}"
        await interaction.response.send_message(message, ephemeral=True)
        return True

    return False


@bot.slash_command()  # pyright: ignore  # still some unknowns in disnake
async def test_button(interaction: disnake.CommandInteraction) -> None:
    component = await FooButton(count=0).as_ui_component()
    await interaction.response.send_message(components=component)


@bot.slash_command()  # pyright: ignore  # still some unknowns in disnake
async def test_nested_button(interaction: disnake.CommandInteraction) -> None:
    component = await FooBarBazButton(count=0).as_ui_component()
    await interaction.response.send_message(components=component)


bot.run(os.getenv("EXAMPLE_TOKEN"))
