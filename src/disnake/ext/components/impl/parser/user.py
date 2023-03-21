"""Parser implementations for disnake user types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base, snowflake

__all__: typing.Sequence[str] = (
    "GetUserParser",
    "GetMemberParser",
    "UserParser",
    "MemberParser",
)


def _get_user(inter: disnake.Interaction, argument: str) -> disnake.User:
    user = inter.bot.get_user(int(argument))

    if user is None:
        msg = f"Could not find a user with id {argument!r}."
        raise LookupError(msg)

    return user


def _get_member(inter: disnake.Interaction, argument: str) -> disnake.Member:
    member = inter.guild.get_member(int(argument)) if inter.guild else None

    if member is None:
        msg = f"Could not find a member with id {argument!r}."
        raise LookupError(msg)

    return member


GetUserParser = base.Parser.from_funcs(
    _get_user, snowflake.snowflake_dumps, is_default_for=(disnake.User,)
)
GetMemberParser = base.Parser.from_funcs(
    _get_member, snowflake.snowflake_dumps, is_default_for=(disnake.Member,)
)


async def _fetch_user(inter: disnake.Interaction, argument: str) -> disnake.User:
    return await inter.bot.fetch_user(int(argument))


async def _fetch_member(inter: disnake.Interaction, argument: str) -> disnake.Member:
    # annotating inter as GuildCommandInteraction results in a typing error
    # since Parser.from_funcs is accepting Interaction so we cast here
    guild = typing.cast(disnake.Guild, inter.guild)
    return await guild.fetch_member(int(argument))


UserParser = base.Parser.from_funcs(
    _fetch_user, snowflake.snowflake_dumps, is_default_for=(disnake.User,)
)
MemberParser = base.Parser.from_funcs(
    _fetch_member, snowflake.snowflake_dumps, is_default_for=(disnake.Member,)
)
