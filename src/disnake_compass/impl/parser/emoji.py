"""Parser implementations for disnake emoji types."""

from __future__ import annotations

import typing

import attrs
import disnake

from disnake_compass.impl.parser import base as parser_base
from disnake_compass.impl.parser import builtins as builtins_parsers
from disnake_compass.internal import di

__all__: typing.Sequence[str] = (
    "EmojiParser",
    "PartialEmojiParser",
    "StickerParser",
)


# GET_ONLY


# TODO: Probably need to implement animated, maybe also name
# TODO: Maybe implement some way of *not* requiring ids for partial emoji
@parser_base.register_parser_for(disnake.PartialEmoji)
@attrs.define(slots=True)
class PartialEmojiParser(parser_base.Parser[disnake.PartialEmoji]):
    r"""Parser type with support for partial emoji.

    Parameters
    ----------
    int_parser:
        The :class:`~disnake_compass.impl.parser.builtins.IntParser` to use
        internally for this parser.

    """

    int_parser: builtins_parsers.IntParser = attrs.field(
        factory=lambda: builtins_parsers.IntParser.default(int),
    )
    """The :class:`~disnake_compass.impl.parser.builtins.IntParser` to use
    internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default partial emoji parser will also return compressed results.
    """

    async def loads(self, argument: str, /) -> disnake.PartialEmoji:
        """Load a partial emoji from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a partial emoji.

        """
        return disnake.PartialEmoji.from_dict({"id": self.int_parser.loads(argument)})

    async def dumps(self, argument: disnake.PartialEmoji, /) -> str:
        """Dump a partial emoji into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        if not argument.id:
            msg = "PartialEmojiParser requires PartialEmoji.id to be set."
            raise ValueError(msg)

        return await self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.Emoji)
@attrs.define(slots=True, kw_only=True)
class EmojiParser(parser_base.Parser[disnake.Emoji]):
    """Synchronous parser type with support for emoji.

    Parameters
    ----------
    int_parser:
        The :class:`~disnake_compass.impl.parser.builtins.IntParser` to use
        internally for this parser.
    allow_api_requests:
        Whether or not to allow this parser to make API requests.

    """

    int_parser: builtins_parsers.IntParser = attrs.field(
        factory=lambda: builtins_parsers.IntParser.default(int),
    )
    """The :class:`~disnake_compass.impl.parser.builtins.IntParser` to use
    internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default emoji parser will also return compressed results.
    """
    allow_api_requests: bool = attrs.field(default=True, kw_only=True)
    """Whether or not to allow this parser to make API requests.

    Parsers will always try getting a result from cache first.
    """

    async def loads(self, argument: str, /) -> disnake.Emoji:
        """Load an emoji from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be loaded into an emoji.

        Raises
        ------
        :class:`LookupError`:
            An emoji with the id stored in the ``argument`` could not be found.

        """
        emoji_id = await self.int_parser.loads(argument)
        client = di.resolve_dependency(disnake.Client)

        emoji = client.get_emoji(emoji_id)
        if emoji:
            return emoji

        if self.allow_api_requests:
            guild = di.resolve_dependency(disnake.Guild)
            return await guild.fetch_emoji(emoji_id)

        msg = f"Could not find an emoji with id {emoji_id}."
        raise LookupError(msg)

    async def dumps(self, argument: disnake.Emoji, /) -> str:
        """Dump an emoji into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return await self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.Sticker)
@attrs.define(slots=True, kw_only=True)
class StickerParser(parser_base.Parser[disnake.Sticker]):
    """Synchronous parser type with support for stickers.

    Parameters
    ----------
    int_parser:
        The :class:`~disnake_compass.impl.parser.builtins.IntParser` to use
        internally for this parser.
    allow_api_requests:
        Whether or not to allow this parser to make API requests.

    """

    int_parser: builtins_parsers.IntParser = attrs.field(
        factory=lambda: builtins_parsers.IntParser.default(int),
    )
    """The :class:`~disnake_compass.impl.parser.builtins.IntParser` to use
    internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default emoji parser will also return compressed results.
    """
    allow_api_requests: bool = attrs.field(default=True, kw_only=True)
    """Whether or not to allow this parser to make API requests.

    Parsers will always try getting a result from cache first.
    """

    async def loads(self, argument: str, /) -> disnake.Sticker:
        """Load a sticker from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a sticker.

        Raises
        ------
        :class:`LookupError`:
            A sticker with the id stored in the ``argument`` could not be found.

        """
        client = di.resolve_dependency(disnake.Client)
        sticker_id = await self.int_parser.loads(argument)

        sticker = client.get_sticker(sticker_id)
        if sticker:
            return sticker

        if self.allow_api_requests:
            guild = di.resolve_dependency(disnake.Guild)
            return await guild.fetch_sticker(sticker_id)

        msg = f"Could not find an emoji with id {sticker_id}."
        raise LookupError(msg)

    async def dumps(self, argument: disnake.Sticker, /) -> str:
        """Dump a sticker into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return await self.int_parser.dumps(argument.id)
