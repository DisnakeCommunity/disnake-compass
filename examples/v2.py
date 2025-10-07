import os
import typing
import disnake
import disnake_compass
from disnake.ext import commands


bot = commands.InteractionBot()

manager = disnake_compass.get_manager()
manager.add_to_client(bot)


# This is one big hack
from disnake_compass.impl import manager as cope

async def _temp_update_layout(layout: typing.Sequence[cope.MessageTopLevelComponentV2], rich_components: typing.Sequence[disnake_compass.api.RichComponent]):
    if not rich_components:
        return

    rich_component_iter = iter(rich_components)
    rich_component = next(rich_component_iter)

    # TODO: Maybe store and use numerical id for this?
    for component in disnake.ui.walk_components(layout):
        if isinstance(component, (disnake.ui.Button, disnake.ui.BaseSelect)) and component.custom_id is not None:
            identifier, _ = manager.get_identifier(component.custom_id)
            if identifier == manager.make_identifier(type(rich_component)):
                finalised = await rich_component.as_ui_component(manager)
                component.refresh_component(finalised._underlying)  # Hacky in-place update

                rich_component = next(rich_component_iter, None)
                if rich_component is None:
                    return

@manager.register()
class PageAdvanceButton(disnake_compass.RichButton):

    increment: int

    async def callback(self, inter: disnake.MessageInteraction[disnake.Client]) -> None:
        layout, rich_components = await manager.parse_message_components(inter.message)

        for component in rich_components:
            if isinstance(component, PageTrackerButton):
                component.increment(self.increment)

        await _temp_update_layout(layout, rich_components)
        await inter.response.edit_message(components=layout)


@manager.register()
class PageTrackerButton(disnake_compass.RichButton):
    disabled: bool = True

    page: int
    pages: int

    def __attrs_post_init__(self):
        self.update_label()

    def increment(self, inc: int):
        self.page = (self.page + inc) % self.pages
        self.update_label()

    def update_label(self):
        self.label = f"{self.page+1} / {self.pages}"

    async def callback(self, inter: disnake.MessageInteraction[disnake.Client]) -> None:
        raise NotImplementedError  # This button is always disabled.


async def create_paginator_controls(page: int, pages: int):
    return disnake.ui.Container(
        disnake.ui.ActionRow(
            await PageAdvanceButton(label="<", increment=-1).as_ui_component(manager),
            await PageTrackerButton(page=page, pages=pages).as_ui_component(manager),
            await PageAdvanceButton(label=">", increment=1).as_ui_component(manager),
        )
    )


@bot.slash_command()
async def test_v2(inter: disnake.CommandInteraction):
    controls = await create_paginator_controls(0,3)

    await inter.response.send_message(components=[controls])


bot.run(os.getenv("EXAMPLE_TOKEN"))
