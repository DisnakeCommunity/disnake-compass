"""Parser implementations for disnake message types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base as parser_base
from disnake.ext.components.impl.parser import helpers, snowflake

__all__: typing.Sequence[str] = (
    "GetMessageParser",
    "MessageParser",
    "PartialMessageParser",
)

AnyChannel = typing.Union[
    disnake.TextChannel,
    disnake.Thread,
    disnake.VoiceChannel,
    disnake.DMChannel,
    disnake.PartialMessageable,
]


class GetMessageParser(  # noqa: D101
    parser_base.Parser[disnake.Message], is_default_for=(disnake.Message,)
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    def loads(  # noqa: D102
        self,
        source: typing.Union[helpers.BotAware, helpers.MessageAware],
        argument: str,
    ) -> disnake.Message:
        if isinstance(source, helpers.BotAware):
            message = source.bot.get_message(int(argument))
            if message:
                return message

            if isinstance(source, helpers.MessageAware):
                return source.message

        else:
            return source.message

        msg = f"Could not find a message with id {argument!r}."
        raise LookupError(msg)


class MessageParser(  # noqa: D101
    parser_base.Parser[disnake.Message],
    is_default_for=(disnake.Message,),
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    async def loads(  # noqa: D102
        self, source: helpers.ChannelAware, argument: str
    ) -> disnake.Message:
        # <<docstring inherited from parser_api.Parser>>

        if isinstance(source, helpers.BotAware):
            message = source.bot.get_message(int(argument))
            if message:
                return message

        return await source.channel.fetch_message(int(argument))


class PartialMessageParser(  # noqa: D101
    parser_base.Parser[disnake.PartialMessage], is_default_for=(disnake.PartialMessage,)
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self, channel: typing.Optional[AnyChannel] = None) -> None:
        self.channel = channel
        self.dumps = snowflake.snowflake_dumps

    def loads(  # noqa: D102
        self, source: helpers.ChannelAware, argument: str
    ) -> disnake.PartialMessage:
        # <<docstring inherited from parser_api.Parser>>

        return disnake.PartialMessage(
            channel=self.channel or source.channel, id=int(argument)
        )
