"""Parser implementations for basic disnake snowflake types."""

from __future__ import annotations

import typing

import attrs
import disnake

from disnake_compass.impl.parser import base as parser_base
from disnake_compass.impl.parser import builtins as builtins_parsers

__all__: typing.Sequence[str] = ("SnowflakeParser",)


@parser_base.register_parser_for(disnake.abc.Snowflake, disnake.Object)
@attrs.define(slots=True)
class SnowflakeParser(parser_base.Parser[disnake.abc.Snowflake]):
    r"""Parser implementation for :class:`disnake.abc.Snowflake`\s.

    .. note::
        As snowflakes are abstact, :meth:`loads` returns a
        :class:`disnake.Object` instead.

    Parameters
    ----------
    int_parser:
        The :class:`IntParser` to use internally for this parser.

    """

    int_parser: builtins_parsers.IntParser = attrs.field(
        factory=lambda: builtins_parsers.IntParser.default(int),
    )
    """The :class:`~disnake_compass.impl.parser.builtins.IntParser` to use
    internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default guild parser will also return compressed results.
    """

    async def loads(self, argument: str, /) -> disnake.Object:
        """Load a snowflake from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a floating point number.

        """
        return disnake.Object(await self.int_parser.loads(argument))

    async def dumps(self, argument: disnake.abc.Snowflake, /) -> str:
        """Dump a snowflake into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return await self.int_parser.dumps(argument.id)
