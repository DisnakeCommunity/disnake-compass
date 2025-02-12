"""Parser implementations for disnake message types."""

from __future__ import annotations

import contextlib
import typing

import disnake
from disnake.ext.components.impl.parser import base as parser_base
from disnake.ext.components.impl.parser import builtins as builtins_parsers
from disnake.ext.components.internal import di

__all__: typing.Sequence[str] = ("MessageParser", "PartialMessageParser")

AnyChannel = typing.Union[
    disnake.TextChannel,
    disnake.Thread,
    disnake.VoiceChannel,
    disnake.DMChannel,
    disnake.PartialMessageable,
]


@parser_base.register_parser_for(disnake.PartialMessage)
class PartialMessageParser(parser_base.Parser[disnake.PartialMessage]):
    r"""Parser type with support for partial messages.

    Parameters
    ----------
    int_parser:
        The :class:`~components.impl.parser.builtins.IntParser` to use
        internally for this parser.
    channel:
        The channel in which to make the partial message.

        Defaults to ``None``. If left to be ``None``, :meth:`loads` will
        attempt to get a channel from the ``source``.

    """

    int_parser: builtins_parsers.IntParser
    """The :class:`~components.impl.parser.builtins.IntParser` to use
    internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default message parser will also return compressed results.
    """
    channel: typing.Optional[AnyChannel]
    """The channel in which to make the partial message."""

    def __init__(
        self,
        int_parser: typing.Optional[builtins_parsers.IntParser] = None,
        *,
        channel: typing.Optional[AnyChannel] = None,
    ) -> None:
        self.int_parser = int_parser or builtins_parsers.IntParser.default(int)
        self.channel = channel

    async def loads(self, argument: str, /) -> disnake.PartialMessage:
        """Load a partial message from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a partial message.
        source:
            The source to use for parsing.

            If :attr:`channel` is set, the source is ignored. Otherwise, this
            must be a channel, or be a type that has access to a
            :class:`channel <disnake.TextChannel>` attribute.

            .. note::
                This can be any channel type that supports
                `get_partial_message`.

        Raises
        ------
        :class:`RuntimeError`:
            :attr:`channel` was not set, and no channel could be obtained from
            the ``source``.

        """
        channel = (
            self.channel
            # TODO: Check if we can do something with a protocol here,
            #       I think a protocol with only a `get_partial_message` method
            #       should work?
            or di.resolve_dependency(disnake.TextChannel, None)
            or di.resolve_dependency(disnake.Thread, None)
            or di.resolve_dependency(disnake.VoiceChannel, None)
            or di.resolve_dependency(disnake.DMChannel, None)
            or di.resolve_dependency(disnake.PartialMessageable, None)
        )

        if not channel:
            msg = (
                "A channel must be provided either through self.channel or"
                " dependency injection, got neither."
            )
            raise RuntimeError(msg)

        return channel.get_partial_message(await self.int_parser.loads(argument))

    async def dumps(self, argument: disnake.PartialMessage, /) -> str:
        """Dump a partial message into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return await self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.Message)
class MessageParser(parser_base.Parser[disnake.Message]):
    r"""Asynchronous parser type with support for messages.

    .. warning::
        This parser can make API requests.

    Parameters
    ----------
    int_parser:
        The :class:`~components.impl.parser.builtins.IntParser` to use
        internally for this parser.
    allow_api_requests:
        Whether or not to allow this parser to make API requests.

    """

    int_parser: builtins_parsers.IntParser
    """The :class:`~components.impl.parser.builtins.IntParser` to use
    internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default message parser will also return compressed results.
    """
    allow_api_requests: bool
    """Whether or not to allow this parser to make API requests.

    Parsers will always try getting a result from cache first.
    """

    def __init__(
        self,
        int_parser: typing.Optional[builtins_parsers.IntParser] = None,
        *,
        allow_api_requests: bool = False,
    ) -> None:
        self.int_parser = int_parser or builtins_parsers.IntParser.default(int)
        self.allow_api_requests = allow_api_requests

    async def loads(self, argument: str, /) -> disnake.Message:
        """Load a message from a string.

        This uses the underlying :attr:`int_parser`.

        This method first tries to get the message from cache. If this fails,
        it will try to fetch the message instead.

        .. warning::
            This method can make API requests.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a message.

        Raises
        ------
        :class:`LookupError`:
            A message with the id stored in the ``argument`` could not be found.

        """
        message_id = await self.int_parser.loads(argument)

        maybe_message = di.resolve_dependency(disnake.Message, None)
        if maybe_message and maybe_message.id == message_id:
            return maybe_message

        maybe_client = di.resolve_dependency(disnake.Client, None)
        if maybe_client:
            message = maybe_client.get_message(message_id)
            if message:
                return message

        if self.allow_api_requests:
            maybe_messageable = di.resolve_dependency(disnake.abc.Messageable, None)
            if maybe_messageable:
                with contextlib.suppress(disnake.HTTPException):
                    return await maybe_messageable.fetch_message(message_id)

        msg = f"Could not find a message with id {argument!r}."
        raise LookupError(msg)

    async def dumps(self, argument: disnake.Message, /) -> str:
        """Dump a message into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return await self.int_parser.dumps(argument.id)
