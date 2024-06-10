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


class GetUserParser(  # noqa: D101
    base.Parser[disnake.User],
    is_default_for=(disnake.User, disnake.abc.User),
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    def loads(  # noqa: D102
        self, inter: disnake.Interaction, argument: str
    ) -> disnake.User:
        # <<docstring inherited from parser_api.Parser>>

        user = inter.bot.get_user(int(argument))

        if user is None:
            msg = f"Could not find a user with id {argument!r}."
            raise LookupError(msg)

        return user


class GetMemberParser(  # noqa: D101
    base.Parser[disnake.Member],
    is_default_for=(disnake.Member,),
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    def loads(  # noqa: D102
        self, inter: disnake.Interaction, argument: str
    ) -> disnake.Member:
        # <<docstring inherited from parser_api.Parser>>

        if inter.guild is None:
            msg = (
                "Impossible to get a member from an"
                " interaction that doesn't come from a guild."
            )
            raise TypeError(msg)
        member = inter.guild.get_member(int(argument))

        if member is None:
            msg = f"Could not find a member with id {argument!r}."
            raise LookupError(msg)

        return member


class UserParser(  # noqa: D101
    base.Parser[disnake.User], is_default_for=(disnake.User, disnake.abc.User)
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    async def loads(  # noqa: D102
        self, inter: disnake.Interaction, argument: str
    ) -> disnake.User:
        # <<docstring inherited from parser_api.Parser>>

        return (
            inter.bot.get_user(int(argument))
            or await inter.bot.fetch_user(int(argument))
        )  # fmt: skip


class MemberParser(  # noqa: D101
    base.Parser[disnake.Member], is_default_for=(disnake.Member,)
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    async def loads(  # noqa: D102
        self, inter: disnake.Interaction, argument: str
    ) -> disnake.Member:
        # <<docstring inherited from parser_api.Parser>>

        if inter.guild is None:
            msg = (
                "Impossible to fetch a member from an"
                " interaction that doesn't come from a guild."
            )
            raise TypeError(msg)
        return (
            inter.guild.get_member(int(argument))
            or await inter.guild.fetch_member(int(argument))
        )  # fmt: skip
