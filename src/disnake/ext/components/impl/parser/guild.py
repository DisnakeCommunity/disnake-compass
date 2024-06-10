"""Parser implementations for disnake.Guild type."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base, snowflake

__all__: typing.Sequence[str] = ("GuildParser", "GetGuildParser")


class GetGuildParser(  # noqa: D101
    base.Parser[disnake.Guild],
    is_default_for=(disnake.Guild,),
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    def loads(  # noqa: D102
        self, inter: disnake.Interaction, argument: str
    ) -> disnake.Guild:
        # <<docstring inherited from parser_api.Parser>>

        guild = inter.bot.get_guild(int(argument))

        if guild is None:
            msg = f"Could not find a guild with id {argument!r}."
            raise LookupError(msg)

        return guild


class GuildParser(  # noqa: D101
    base.Parser[disnake.Guild],
    is_default_for=(disnake.Guild,),
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    async def loads(  # noqa: D102
        self, inter: disnake.Interaction, argument: str
    ) -> disnake.Guild:
        # <<docstring inherited from parser_api.Parser>>

        return (
            inter.bot.get_guild(int(argument))
            or await inter.bot.fetch_guild(int(argument))
        )  # fmt: skip
