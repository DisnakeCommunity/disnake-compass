"""Parser implementations for basic disnake snowflake types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base

__all__: typing.Sequence[str] = ("ObjectParser",)


def snowflake_dumps(argument: disnake.abc.Snowflake) -> str:
    """Dump any kind of :class:`disnake.abc.Snowflake` to a string."""
    return str(argument.id)


class ObjectParser(  # noqa: D101
    base.Parser[disnake.Object],
    is_default_for=(disnake.abc.Snowflake, disnake.Object),
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake_dumps

    def loads(  # noqa: D102
        self, _: disnake.Interaction, argument: str
    ) -> disnake.Object:
        return disnake.Object(int(argument))
