"""Parser implementations for disnake role types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base as parser_base
from disnake.ext.components.impl.parser import helpers, snowflake

__all__: typing.Sequence[str] = (
    "GetRoleParser",
    "RoleParser",
)


class GetRoleParser(  # noqa: D101
    parser_base.Parser[disnake.Role],
    is_default_for=(disnake.Role,),
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    def loads(  # noqa: D102
        self,
        source: typing.Union[
            helpers.GuildAware,
            helpers.MessageAware,
            helpers.ChannelAware,
        ],
        argument: str,
    ) -> disnake.Role:
        # <<docstring inherited from parser_api.Parser>>

        guild = None
        if isinstance(source, helpers.GuildAware):
            guild = source.guild

        if guild is None and isinstance(source, helpers.MessageAware):
            guild = source.message.guild

        if (
            guild is None
            and isinstance(source, helpers.ChannelAware)
            and isinstance(source.channel, helpers.GuildAware)
        ):
            guild = source.channel.guild

        if guild is None:
            msg = "Cannot get a role from an object that doesn't reference a guild."
            raise TypeError(msg)

        role = guild.get_role(int(argument))
        if role is not None:
            return role

        msg = f"Could not find a role with id {argument!r}."
        raise LookupError(msg)


class RoleParser(  # noqa: D101
    parser_base.Parser[disnake.Role],
    is_default_for=(disnake.Role,),
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    async def loads(  # noqa: D102
        self,
        source: typing.Union[
            helpers.GuildAware,
            helpers.MessageAware,
            helpers.ChannelAware,
        ],
        argument: str,
    ) -> disnake.Role:
        # <<docstring inherited from parser_api.Parser>>

        guild = None
        if isinstance(source, helpers.GuildAware):
            guild = source.guild

        if guild is None and isinstance(source, helpers.MessageAware):
            guild = source.message.guild

        if (
            guild is None
            and isinstance(source, helpers.ChannelAware)
            and isinstance(source.channel, helpers.GuildAware)
        ):
            guild = source.channel.guild

        if guild is None:
            msg = "Cannot get a role from an object that doesn't reference a guild."
            raise TypeError(msg)

        id_ = int(argument)
        role = guild.get_role(id_)
        if role is not None:
            return role

        for role in await guild.fetch_roles():
            if role.id == id_:
                return role

        # a role id coming from a custom_id could be of a deleted role object
        # so we're handling that possibility
        if role is None:
            msg = f"Could not find a role with id {argument!r}."
            raise LookupError(msg)

        return role
