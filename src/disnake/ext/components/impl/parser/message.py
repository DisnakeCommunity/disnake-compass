"""Parser implementations for disnake message types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base, snowflake

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
    base.Parser[disnake.Message], is_default_for=(disnake.Message,)
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    def loads(  # noqa: D102
        self, inter: disnake.Interaction, argument: str
    ) -> disnake.Message:
        # <<docstring inherited from parser_api.Parser>>

        message = inter.bot.get_message(int(argument))

        if message is None:
            msg = f"Could not find a message with id {argument!r}."
            raise LookupError(msg)

        return message


class MessageParser(  # noqa: D101
    base.Parser[disnake.Message],
    is_default_for=(disnake.Message,),
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    async def loads(  # noqa: D102
        self, inter: disnake.Interaction, argument: str
    ) -> disnake.Message:
        # <<docstring inherited from parser_api.Parser>>

        return (
            inter.bot.get_message(int(argument))
            or await inter.channel.fetch_message(int(argument))
        )  # fmt: skip


class PartialMessageParser(  # noqa: D101
    base.Parser[disnake.PartialMessage], is_default_for=(disnake.PartialMessage,)
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self, channel: typing.Optional[AnyChannel] = None) -> None:
        self.channel = channel
        self.dumps = snowflake.snowflake_dumps

    def loads(  # noqa: D102
        self, inter: disnake.Interaction, argument: str
    ) -> disnake.PartialMessage:
        # <<docstring inherited from parser_api.Parser>>

        return disnake.PartialMessage(
            channel=self.channel or inter.channel, id=int(argument)
        )
