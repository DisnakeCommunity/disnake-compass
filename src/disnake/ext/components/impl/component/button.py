"""Default implementation of button-based components."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components import fields, interaction
from disnake.ext.components.api import component as component_api
from disnake.ext.components.impl.component import base as component_base

__all__: typing.Sequence[str] = ("RichButton",)


_AnyEmoji = typing.Union[str, disnake.PartialEmoji, disnake.Emoji]


# God knows why this is needed, but if I don't do this, classes inheriting from
# RichButton see e.g. `fields.internal(default=None)` in the init signature.
internal = fields.internal


@typing.runtime_checkable
class RichButton(
    component_api.RichButton, component_base.ComponentBase, typing.Protocol
):
    """The default implementation of a disnake-ext-components button.

    This works similar to a dataclass, but with some extra things to take into
    account.

    First and foremost, there are class variables for :attr:`label`,
    :attr:`style`, :attr:`emoji` and :attr:`disabled`. These set the
    corresponding attributes on the button class when they are sent to discord,
    and are meant to be overwritten by the user.

    Next, fields can be defined similarly to dataclasses, by means of a name,
    a type annotation, and an optional :func:`components.field` to set the
    default or a custom parser.

    Classes created in this way have auto-generated slots and an auto-generated
    ``__init__``. The init-signature contains all the custom id fields as
    keyword-only arguments.
    """

    event = "on_button_click"

    label: typing.Optional[str] = fields.internal(default=None)
    style: disnake.ButtonStyle = fields.internal(default=disnake.ButtonStyle.secondary)
    emoji: typing.Optional[_AnyEmoji] = fields.internal(default=None)
    disabled: bool = fields.internal(default=False)

    async def as_ui_component(self) -> disnake.ui.Button[None]:  # noqa: D102
        # <<docstring inherited from component_api.RichButton>>

        if not self.manager:
            message = "Cannot serialise components without a manager."
            raise RuntimeError(message)

        return disnake.ui.Button(
            style=self.style,
            label=self.label,
            disabled=self.disabled,
            emoji=self.emoji,
            custom_id=await self.manager.make_custom_id(self),
        )

    async def callback(  # pyright: ignore[reportIncompatibleMethodOverride]  # noqa: D102
        self,
        __inter: interaction.MessageInteraction,
    ) -> None:
        # <<docstring inherited from component_api.RichButton>>

        # NOTE: We narrow the interaction type down to a disnake.MessageInteraction
        #       here. This isn't typesafe, but it's just cleaner for the user.
        ...
