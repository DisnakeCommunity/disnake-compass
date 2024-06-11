"""Parser implementations for basic disnake snowflake types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base as parser_base

__all__: typing.Sequence[str] = ("SnowflakeParser",)


def snowflake_dumps(argument: disnake.abc.Snowflake) -> str:
    """Dump any kind of :class:`disnake.abc.Snowflake` to a string."""
    return str(argument.id)


class SnowflakeParser(  # noqa: D101
    parser_base.Parser[disnake.Object],
    is_default_for=(disnake.abc.Snowflake, disnake.Object),
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake_dumps

    def loads(self, _: object, argument: str) -> disnake.Object:  # noqa: D102
        return disnake.Object(int(argument))


ObjectParser = SnowflakeParser  # TODO: Remove.
