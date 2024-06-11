"""Default implementation of select-based components."""

from __future__ import annotations

import typing

import attr
import disnake
from disnake.ext.components import fields, interaction
from disnake.ext.components.api import component as component_api
from disnake.ext.components.impl.component import base as component_base

__all__: typing.Sequence[str] = (
    "RichStringSelect",
    "RichUserSelect",
    "RichRoleSelect",
    "RichMentionableSelect",
    "RichChannelSelect",
)

# God knows why this is needed, but if I don't do this, classes inheriting from
# RichSelect see e.g. `placeholder: str = fields.internal(default=None)` in the
# init signature.
internal = fields.internal


class BaseSelect(
    component_api.RichSelect, component_base.ComponentBase, typing.Protocol
):
    """The base class of a disnake-ext-components selects.

    For implementations, see :class:`RichStringSelect`, :class:`RichUserSelect`,
    :class:`RichRoleSelect`, :class:`RichMentionableSelect`,
    :class:`RichChannelSelect`.
    """

    event = "on_dropdown"

    placeholder: typing.Optional[str] = fields.internal(default=None)
    min_values: int = fields.internal(default=1)
    max_values: int = fields.internal(default=1)
    disabled: bool = fields.internal(default=False)

    async def callback(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, __inter: interaction.MessageInteraction
    ) -> None:
        # <<docstring inherited from component_api.RichButton>>

        # NOTE: We narrow the interaction type down to a disnake.MessageInteraction
        #       here. This isn't typesafe, but it's just cleaner for the user.
        ...


class RichStringSelect(BaseSelect, typing.Protocol):
    """The default implementation of a disnake-ext-components string select.

    This works similar to a dataclass, but with some extra things to take into
    account.

    First and foremost, there are class variables for :attr:`placeholder`,
    :attr:`min_values`, :attr:`max_values`, :attr:`disabled`, and:attr:`options`.
    These set the corresponding attributes on the select class when they are
    sent to discord, and are meant to be overwritten by the user.

    Fields can be defined similarly to dataclasses, by means of a name, a type
    annotation, and an optional :func:`components.field` to set the default or
    a custom parser. The options field specifically is designated with
    :func:`components.options` instead.

    Classes created in this way have auto-generated slots and an auto-generated
    ``__init__``. The init-signature contains all the custom id fields as
    keyword-only arguments.
    """

    options: typing.List[disnake.SelectOption] = fields.internal(
        default=attr.Factory(list)  # pyright: ignore
    )

    async def as_ui_component(self) -> disnake.ui.StringSelect[None]:  # noqa: D102
        # <<docstring inherited from component_api.RichButton>>

        if not self.manager:
            message = "Cannot serialise components without a manager."
            raise RuntimeError(message)

        return disnake.ui.StringSelect(
            placeholder=self.placeholder,
            min_values=self.min_values,
            max_values=self.max_values,
            disabled=self.disabled,
            options=self.options,
            custom_id=await self.manager.make_custom_id(self),
        )


class RichUserSelect(BaseSelect, typing.Protocol):
    """The default implementation of a disnake-ext-components user select.

    This works similar to a dataclass, but with some extra things to take into
    account.

    First and foremost, there are class variables for :attr:`placeholder`,
    :attr:`min_values`, :attr:`max_values`, :attr:`disabled`.
    These set the corresponding attributes on the select class when they are
    sent to discord, and are meant to be overwritten by the user.

    Fields can be defined similarly to dataclasses, by means of a name, a type
    annotation, and an optional :func:`components.field` to set the default or
    a custom parser. The options field specifically is designated with
    :func:`components.options` instead.

    Classes created in this way have auto-generated slots and an auto-generated
    ``__init__``. The init-signature contains all the custom id fields as
    keyword-only arguments.
    """

    async def as_ui_component(self) -> disnake.ui.UserSelect[None]:  # noqa: D102
        # <<docstring inherited from component_api.RichButton>>

        if not self.manager:
            message = "Cannot serialise components without a manager."
            raise RuntimeError(message)

        return disnake.ui.UserSelect(
            placeholder=self.placeholder,
            min_values=self.min_values,
            max_values=self.max_values,
            disabled=self.disabled,
            custom_id=await self.manager.make_custom_id(self),
        )


class RichRoleSelect(BaseSelect, typing.Protocol):
    """The default implementation of a disnake-ext-components role select.

    This works similar to a dataclass, but with some extra things to take into
    account.

    First and foremost, there are class variables for :attr:`placeholder`,
    :attr:`min_values`, :attr:`max_values`, :attr:`disabled`.
    These set the corresponding attributes on the select class when they are
    sent to discord, and are meant to be overwritten by the user.

    Fields can be defined similarly to dataclasses, by means of a name, a type
    annotation, and an optional :func:`components.field` to set the default or
    a custom parser. The options field specifically is designated with
    :func:`components.options` instead.

    Classes created in this way have auto-generated slots and an auto-generated
    ``__init__``. The init-signature contains all the custom id fields as
    keyword-only arguments.
    """

    async def as_ui_component(self) -> disnake.ui.RoleSelect[None]:  # noqa: D102
        # <<docstring inherited from component_api.RichButton>>

        if not self.manager:
            message = "Cannot serialise components without a manager."
            raise RuntimeError(message)

        return disnake.ui.RoleSelect(
            placeholder=self.placeholder,
            min_values=self.min_values,
            max_values=self.max_values,
            disabled=self.disabled,
            custom_id=await self.manager.make_custom_id(self),
        )


class RichMentionableSelect(BaseSelect, typing.Protocol):
    """The default implementation of a disnake-ext-components mentionable select.

    This works similar to a dataclass, but with some extra things to take into
    account.

    First and foremost, there are class variables for :attr:`placeholder`,
    :attr:`min_values`, :attr:`max_values`, :attr:`disabled`.
    These set the corresponding attributes on the select class when they are
    sent to discord, and are meant to be overwritten by the user.

    Fields can be defined similarly to dataclasses, by means of a name, a type
    annotation, and an optional :func:`components.field` to set the default or
    a custom parser. The options field specifically is designated with
    :func:`components.options` instead.

    Classes created in this way have auto-generated slots and an auto-generated
    ``__init__``. The init-signature contains all the custom id fields as
    keyword-only arguments.
    """

    async def as_ui_component(self) -> disnake.ui.MentionableSelect[None]:  # noqa: D102
        # <<docstring inherited from component_api.RichButton>>

        if not self.manager:
            message = "Cannot serialise components without a manager."
            raise RuntimeError(message)

        return disnake.ui.MentionableSelect(
            placeholder=self.placeholder,
            min_values=self.min_values,
            max_values=self.max_values,
            disabled=self.disabled,
            custom_id=await self.manager.make_custom_id(self),
        )


class RichChannelSelect(BaseSelect, typing.Protocol):
    """The default implementation of a disnake-ext-components channel select.

    This works similar to a dataclass, but with some extra things to take into
    account.

    First and foremost, there are class variables for :attr:`channel_types`,
    :attr:`placeholder`, :attr:`min_values`, :attr:`max_values`, :attr:`disabled`.
    These set the corresponding attributes on the select class when they are
    sent to discord, and are meant to be overwritten by the user.

    Fields can be defined similarly to dataclasses, by means of a name, a type
    annotation, and an optional :func:`components.field` to set the default or
    a custom parser. The options field specifically is designated with
    :func:`components.options` instead.

    Classes created in this way have auto-generated slots and an auto-generated
    ``__init__``. The init-signature contains all the custom id fields as
    keyword-only arguments.
    """

    channel_types: typing.Optional[typing.List[disnake.ChannelType]] = fields.internal(
        default=None
    )

    async def as_ui_component(self) -> disnake.ui.ChannelSelect[None]:  # noqa: D102
        # <<docstring inherited from component_api.RichButton>>

        if not self.manager:
            message = "Cannot serialise components without a manager."
            raise RuntimeError(message)

        return disnake.ui.ChannelSelect(
            channel_types=self.channel_types,
            placeholder=self.placeholder,
            min_values=self.min_values,
            max_values=self.max_values,
            disabled=self.disabled,
            custom_id=await self.manager.make_custom_id(self),
        )
