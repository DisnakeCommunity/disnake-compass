"""Default implementation of select-based components."""

from __future__ import annotations

import typing

import attrs
import disnake

from disnake_compass import fields
from disnake_compass.api import component as component_api
from disnake_compass.impl.component import base as component_base

__all__: typing.Sequence[str] = (
    "RichChannelSelect",
    "RichMentionableSelect",
    "RichRoleSelect",
    "RichStringSelect",
    "RichUserSelect",
)


class BaseSelect(
    component_api.RichSelect,
    component_base.ComponentBase,
    typing.Protocol,
):
    """The base class of a disnake-compass select menu.

    For implementations, see :class:`RichStringSelect`, :class:`RichUserSelect`,
    :class:`RichRoleSelect`, :class:`RichMentionableSelect`,
    :class:`RichChannelSelect`.
    """

    event: typing.ClassVar[str] = "on_dropdown"

    placeholder: str | None = fields.internal(default=None)
    min_values: int = fields.internal(default=1)
    max_values: int = fields.internal(default=1)
    disabled: bool = fields.internal(default=False)


class RichStringSelect(BaseSelect, typing.Protocol):
    """The default implementation of a disnake-compass string select.

    This works similar to a dataclass, but with some extra things to take into
    account.

    First and foremost, there are class variables for :attr:`placeholder`,
    :attr:`min_values`, :attr:`max_values`, :attr:`disabled`, and:attr:`options`.
    These set the corresponding attributes on the select class when they are
    sent to discord, and are meant to be overwritten by the user.

    Fields can be defined similarly to dataclasses, by means of a name, a type
    annotation, and an optional :func:`disnake_compass.field` to set the default or
    a custom parser. The options field specifically is designated with
    :func:`disnake_compass.options` instead.

    Classes created in this way have auto-generated slots and an auto-generated
    ``__init__``. The init-signature contains all the custom id fields as
    keyword-only arguments.
    """

    options: list[disnake.SelectOption] = fields.internal(
        default=attrs.Factory(list[disnake.SelectOption]),
    )
    """The options for this select menu.

    Must be a list of between 1 and 25 strings.
    """

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
    """The default implementation of a disnake-compass user select.

    This works similar to a dataclass, but with some extra things to take into
    account.

    First and foremost, there are class variables for :attr:`placeholder`,
    :attr:`min_values`, :attr:`max_values`, :attr:`disabled`.
    These set the corresponding attributes on the select class when they are
    sent to discord, and are meant to be overwritten by the user.

    Fields can be defined similarly to dataclasses, by means of a name, a type
    annotation, and an optional :func:`disnake_compass.field` to set the default or
    a custom parser. The options field specifically is designated with
    :func:`disnake_compass.options` instead.

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
    """The default implementation of a disnake-compass role select.

    This works similar to a dataclass, but with some extra things to take into
    account.

    First and foremost, there are class variables for :attr:`placeholder`,
    :attr:`min_values`, :attr:`max_values`, :attr:`disabled`.
    These set the corresponding attributes on the select class when they are
    sent to discord, and are meant to be overwritten by the user.

    Fields can be defined similarly to dataclasses, by means of a name, a type
    annotation, and an optional :func:`disnake_compass.field` to set the default or
    a custom parser. The options field specifically is designated with
    :func:`disnake_compass.options` instead.

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
    """The default implementation of a disnake-compass mentionable select.

    This works similar to a dataclass, but with some extra things to take into
    account.

    First and foremost, there are class variables for :attr:`placeholder`,
    :attr:`min_values`, :attr:`max_values`, :attr:`disabled`.
    These set the corresponding attributes on the select class when they are
    sent to discord, and are meant to be overwritten by the user.

    Fields can be defined similarly to dataclasses, by means of a name, a type
    annotation, and an optional :func:`disnake_compass.field` to set the default or
    a custom parser. The options field specifically is designated with
    :func:`disnake_compass.options` instead.

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
    """The default implementation of a disnake-compass channel select.

    This works similar to a dataclass, but with some extra things to take into
    account.

    First and foremost, there are class variables for :attr:`channel_types`,
    :attr:`placeholder`, :attr:`min_values`, :attr:`max_values`, :attr:`disabled`.
    These set the corresponding attributes on the select class when they are
    sent to discord, and are meant to be overwritten by the user.

    Fields can be defined similarly to dataclasses, by means of a name, a type
    annotation, and an optional :func:`disnake_compass.field` to set the default or
    a custom parser. The options field specifically is designated with
    :func:`disnake_compass.options` instead.

    Classes created in this way have auto-generated slots and an auto-generated
    ``__init__``. The init-signature contains all the custom id fields as
    keyword-only arguments.
    """

    channel_types: list[disnake.ChannelType] | None = fields.internal(
        default=None,
    )
    """The channel types to allow for this select menu.

    Defaults to :obj:`None`, implying all channel types are allowed.
    """

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
