"""A simple example on the use of component managers with disnake-ext-components."""

import os
import typing

import disnake
from disnake.ext import commands, components

# First and foremost, we create a bot as per usual. Since we don't need any
# prefix command capabilities, we opt for an InteractionBot.
bot = commands.InteractionBot()


# A call to get_manager without arguments returns the root manager.
# We register the root manager to the bot, which will ensure all components
# we register to any other manager will automatically be handled. This is
# because a manager handles its own components along with any of its children's.
manager = components.get_manager()
manager.add_to_bot(bot)


# We can create a child manager as follows:
foo_manager = components.get_manager("foo")


# We can go deeper in the parent/child hierarchy by separating them with dots:
deeply_nested_manager = components.get_manager("foo.bar.baz")


# Any missing bits will automatically be filled in-- the above line has
# automatically created a manager named "foo.bar", too.


# Now let us quickly register a button each to our `foo_manager` and our
# `deeply_nested_manager`. To this end, we will use the button example:
@foo_manager.register
class FooButton(components.RichButton):
    label: typing.Optional[str] = "0"

    count: int

    async def callback(self, interaction: components.MessageInteraction) -> None:
        self.count += 1
        self.label = str(self.count)

        await interaction.response.edit_message(components=self)


@deeply_nested_manager.register
class FooBarBazButton(components.RichButton):
    label: typing.Optional[str] = "0"

    count: int

    async def callback(self, interaction: components.MessageInteraction) -> None:
        self.count += 1
        self.label = str(self.count)

        await interaction.response.edit_message(components=self)


# For most use cases, the default implementation of the component manager
# should suffice. Two methods of interest to customise your managers without
# having to subclass them are `ComponentManager.as_callback_wrapper` and
# `ComponentManager.as_error_handler`.

# `ComponentManager.as_callback_wrapper` wraps the callbacks of all components
# registered to that manager along with those of its children. Therefore, if we
# were to add a callback wrapper to the root manager, we would ensure it
# applies to *all* components. For example, say we want to log all component
# interactions:


@manager.as_callback_wrapper
async def wrapper(
    manager: components.ComponentManager,
    component: components.api.RichComponent,
    interaction: disnake.Interaction,
):
    # Any code placed before the yield statement runs before the component
    # callback is invoked.
    # (For actual production code, please use logging instead of print.)
    print(
        f"User {interaction.user.name!r} interacted with component"
        f" {type(component).__name__!r}..."
    )

    yield  # This is where the component (and other wrappers) get to run.

    # Any code placed after the yield statement runs after the component
    # callback is invoked. This can be used for cleanup of resources.
    # Note that any changes made to the component instance by other wrappers
    # and/or the callback itself are reflected here.
    print(
        f"User {interaction.user.name!r}s interaction with component"
        f" {type(component).__name__!r} was successful!"
    )


# This can also be used as a check. By raising an exception before the
# component callback is invoked, you can prevent it from being invoked
# entirely. The exception is then also passed to exception handlers.
class InvalidUserError(Exception):
    def __init__(self, message: str, user: typing.Union[disnake.User, disnake.Member]):
        super().__init__(message)
        self.message = message
        self.user = user


@deeply_nested_manager.as_callback_wrapper
async def check_wrapper(
    manager: components.api.ComponentManager,
    component: components.api.RichComponent,
    interaction: disnake.Interaction,
):
    # For example, let's allow *only* the original slash command author to
    # interact with any components on this manager.
    if (
        # This only applies to message interactions...
        isinstance(interaction, disnake.MessageInteraction)
        # The message must have been sent as interaction response...
        and interaction.message.interaction
        # The component user is NOT the same as the original interaction user...
        and interaction.user != interaction.message.interaction.user
    ):
        # Raise our custom error for convenience.
        message = "You are not allowed to use this component."
        raise InvalidUserError(message, interaction.user)

    yield


# Similarly, we can create an exception handler for our components. An
# exception handler function should return `True` if the error was handled, and
# `False` or `None` otherwise. The default implementation hands the exception
# down to the next handler until it either is handled or reaches the root
# manager. If the root manager is reached (and does not have a custom exception
# handler), the exception is logged.


# To demonstrate the difference, we will make a custom error handler only for
# the `deeply_nested_manager`.
@deeply_nested_manager.as_exception_handler
async def error_handler(
    manager: components.ComponentManager,
    component: components.api.RichComponent,
    interaction: disnake.Interaction,
    exception: Exception,
):
    if isinstance(exception, InvalidUserError):
        message = f"{exception.user.mention}, {exception.message}"
        await interaction.response.send_message(message, ephemeral=True)
        return True  # The exception has been handled.

    return False  # The exception has not been handled.


# Note that you do not need to explicitly return ``False``. Returning ``None``
# is sufficient. Explicitly returning ``False`` is simply preferred for clarity.


# Finally, we send the components to test the managers.
@bot.slash_command()  # pyright: ignore  # still some unknowns in disnake
async def test_button(inter: disnake.CommandInteraction) -> None:
    wrapped = components.wrap_interaction(inter)
    component = FooButton(count=0)

    await wrapped.response.send_message(components=component)


@bot.slash_command()  # pyright: ignore  # still some unknowns in disnake
async def test_nested_button(inter: disnake.CommandInteraction) -> None:
    wrapped = components.wrap_interaction(inter)
    component = FooBarBazButton(count=0)

    await wrapped.response.send_message(components=component)


# Lastly, we run the bot.
bot.run(os.getenv("EXAMPLE_TOKEN"))
