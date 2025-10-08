"""An example showcasing a simple cv2-style paginator powered by disnake-compass."""

import os

import disnake
import disnake_compass
from disnake.ext import commands

bot = commands.InteractionBot()

manager = disnake_compass.get_manager()
manager.add_to_client(bot)


@manager.register()
class PageAdvanceButton(disnake_compass.RichButton):
    increment: int

    async def callback(self, inter: disnake.MessageInteraction[disnake.Client]) -> None:
        _, components = await manager.parse_message_components(inter.message.components)

        # Find and increment the page tracker...
        for component in components:
            if isinstance(component, PageTrackerButton):
                component.increment(self.increment)
                break
        else:
            # Unreachable, a page tracker should always be sent alongside
            # any page advancing buttons.
            raise RuntimeError

        new_page = await create_paginator(component.page, component.pages)
        await inter.response.edit_message(components=new_page)


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

    async def callback(self, _: disnake.MessageInteraction[disnake.Client]) -> None:
        raise NotImplementedError  # This button is always disabled.


def create_paginator_content(page_number: int):
    if page_number == 0:
        return disnake.ui.Section(
            disnake.ui.TextDisplay(
                "Welcome aboard, greenhorn!\nYou are able-bodied and ready for the voyage, I trust?"
            ),
            accessory=disnake.ui.Thumbnail(
                "https://limbuscompany.wiki.gg/images/The_Pequod_Captain_Ishmael_Idle_Sprite.png"
            ),
        )

    if page_number == 1:
        return disnake.ui.Section(
            disnake.ui.TextDisplay("Of course. Has my compass ever led you astray?"),
            accessory=disnake.ui.Thumbnail(
                "https://limbuscompany.wiki.gg/images/The_Pequod_Captain_Ishmael_Evade_Sprite.png"
            ),
        )

    if page_number == 2:
        return disnake.ui.Section(
            disnake.ui.TextDisplay("I'm Fishmael"),
            accessory=disnake.ui.Thumbnail(
                "https://media.tenor.com/mINH1nt-0zgAAAAd/fishmael-limbus-company.gif"
            ),
        )

    msg = f"Unknown page number: {page_number}"
    raise ValueError(msg)


async def create_paginator_controls(page_number: int, pages: int):
    return disnake.ui.ActionRow(
        await PageAdvanceButton(label="<", increment=-1).as_ui_component(),
        await PageTrackerButton(page=page_number, pages=pages).as_ui_component(),
        await PageAdvanceButton(label=">", increment=1).as_ui_component(),
    )


async def create_paginator(page_number: int, pages: int):
    assert page_number < pages

    return disnake.ui.Container(
        disnake.ui.TextDisplay("## Compass"),
        disnake.ui.Separator(),
        create_paginator_content(page_number),
        disnake.ui.Separator(),
        await create_paginator_controls(page_number, pages),
    )


@bot.slash_command()
async def test_v2(inter: disnake.CommandInteraction[disnake.Client]):
    await inter.response.send_message(components=[await create_paginator(0, 3)])


bot.run(os.getenv("EXAMPLE_TOKEN"))
