"""An example showcasing how disnake-compass works with components v2."""

import os

import disnake
from disnake.ext import commands

import disnake_compass

bot = commands.InteractionBot()

manager = disnake_compass.get_manager()
manager.add_to_client(bot)


@manager.register()
class PageAdvanceButton(disnake_compass.RichButton):
    increment: int

    async def callback(self, inter: disnake.MessageInteraction[disnake.Client]) -> None:
        layout, components = await manager.parse_message_components(inter.message.components)

        for component in components:
            if isinstance(component, PageTrackerButton):
                component.increment(self.increment)

        await manager.update_layout(layout, components)
        await inter.response.edit_message(components=layout)


@manager.register()
class PageTrackerButton(disnake_compass.RichButton):
    disabled: bool = True

    page: int
    pages: int

    def __attrs_post_init__(self) -> None:
        self.update_label()

    def increment(self, inc: int):
        self.page = (self.page + inc) % self.pages
        self.update_label()

    def update_label(self):
        self.label = f"{self.page + 1} / {self.pages}"

    async def callback(self, inter: disnake.MessageInteraction[disnake.Client]) -> None:
        raise NotImplementedError  # This button is always disabled.


async def create_paginator_controls(page: int, pages: int):
    return disnake.ui.Container(
        disnake.ui.ActionRow(
            await PageAdvanceButton(label="<", increment=-1).as_ui_component(),
            await PageTrackerButton(page=page, pages=pages).as_ui_component(),
            await PageAdvanceButton(label=">", increment=1).as_ui_component(),
        )
    )


@bot.slash_command()
async def test_v2(inter: disnake.CommandInteraction[disnake.Client]):
    controls = await create_paginator_controls(0, 3)

    await inter.response.send_message(components=[controls])


bot.run(os.getenv("EXAMPLE_TOKEN"))
