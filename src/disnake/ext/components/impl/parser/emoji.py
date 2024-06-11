"""Parser implementations for disnake emoji types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base as parser_base
from disnake.ext.components.impl.parser import helpers, snowflake

__all__: typing.Sequence[str] = (
    "GetEmojiParser",
    "EmojiParser",
    "PartialEmojiParser",
    "GetStickerParser",
    "StickerParser",
)


# GET_ONLY


class GetEmojiParser(  # noqa: D101
    parser_base.Parser[disnake.Emoji],
    is_default_for=(disnake.Emoji,),
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    def loads(  # noqa: D102
        self, source: helpers.BotAware, argument: str
    ) -> disnake.Emoji:
        # <<docstring inherited from parser_api.Parser>>

        emoji = source.bot.get_emoji(int(argument))

        if emoji is None:
            msg = f"Could not find an emoji with id {argument!r}."
            raise LookupError(msg)

        return emoji


class GetStickerParser(  # noqa: D101
    parser_base.Parser[disnake.Sticker],
    is_default_for=(disnake.Sticker,),
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    def loads(  # noqa: D102
        self, source: helpers.BotAware, argument: str
    ) -> disnake.Sticker:
        # <<docstring inherited from parser_api.Parser>>

        sticker = source.bot.get_sticker(int(argument))

        if sticker is None:
            msg = f"Could not find an emoji with id {argument!r}."
            raise LookupError(msg)

        return sticker


# GET AND FETCH


class EmojiParser(  # noqa: D101
    parser_base.Parser[disnake.Emoji],
    is_default_for=(disnake.Emoji,),
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    async def loads(  # noqa: D102
        self, source: helpers.BotAndGuildAware, argument: str
    ) -> disnake.Emoji:
        # <<docstring inherited from parser_api.Parser>>

        if source.guild is None:
            msg = (
                "Impossible to fetch an emoji from an"
                " interaction that doesn't come from a guild."
            )
            raise TypeError(msg)

        return (
            source.bot.get_emoji(int(argument))
            or await source.guild.fetch_emoji(int(argument))
        )  # fmt: skip


class PartialEmojiParser(  # noqa: D101
    parser_base.Parser[disnake.PartialEmoji],
    is_default_for=(disnake.PartialEmoji,),
):
    # <<docstring inherited from parser_api.Parser>>

    def dumps(self, __argument: disnake.PartialEmoji) -> str:  # noqa: D102
        # <<docstring inherited from parser_api.Parser>>

        return str(__argument.id)

    def loads(self, _: object, argument: str) -> disnake.PartialEmoji:  # noqa: D102
        return disnake.PartialEmoji.from_dict({"id": int(argument)})


class StickerParser(  # noqa: D101
    parser_base.Parser[disnake.Sticker],
    is_default_for=(disnake.Sticker,),
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    async def loads(  # noqa: D102
        self, source: helpers.BotAndGuildAware, argument: str
    ) -> disnake.Sticker:
        # <<docstring inherited from parser_api.Parser>>

        if source.guild is None:
            msg = (
                "Impossible to fetch a sticker from an"
                " interaction that doesn't come from a guild."
            )
            raise TypeError(msg)
        return (
            source.bot.get_sticker(int(argument))
            or await source.guild.fetch_sticker(int(argument))
        )  # fmt: skip
