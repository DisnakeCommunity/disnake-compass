"""Parser implementations for disnake channel types."""

from __future__ import annotations

import contextlib
import typing

import attrs
import disnake

from disnake_compass.impl.parser import base as parser_base
from disnake_compass.impl.parser import builtins as builtins_parsers
from disnake_compass.internal import di

__all__: typing.Sequence[str] = (
    "CategoryParser",
    "DMChannelParser",
    "ForumChannelParser",
    "GroupChannelParser",
    "GuildChannelParser",
    "NewsChannelParser",
    "PartialMessageableParser",
    "PrivateChannelParser",
    "StageChannelParser",
    "TextChannelParser",
    "ThreadParser",
    "VoiceChannelParser",
)


_AnyChannel: typing.TypeAlias = (
    disnake.abc.GuildChannel | disnake.abc.PrivateChannel | disnake.Thread
)
_ChannelT = typing.TypeVar("_ChannelT", bound=_AnyChannel)


# NOTE: Making these protocols messes with documentation of all subclasses'
#       __init__ methods.
@attrs.define(slots=True, init=False)
class ChannelParserBase(parser_base.Parser[_ChannelT]):
    r"""Base class for synchronous parser types with support for channels.

    .. note::
        This class cannot be instantiated.

    Parameters
    ----------
    int_parser:
        The :class:`~disnake_compass.impl.parser.builtins.IntParser` to use
        internally for this parser.
    allow_api_requests:
        Whether or not to allow this parser to make API requests.

    """

    parser_type: type[_ChannelT]  # NOTE: Intentionally undocumented.
    int_parser: builtins_parsers.IntParser
    """The :class:`~disnake_compass.impl.parser.builtins.IntParser` to use
    internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default channel parser will also return compressed results.
    """
    allow_api_requests: bool
    """Whether or not to allow this parser to make API requests.

    Parsers will always try getting a result from cache first.
    """

    def __init__(
        self,
        int_parser: builtins_parsers.IntParser | None = None,
        *,
        allow_api_requests: bool = True,
    ) -> None:
        if type(self) is ChannelParserBase:
            msg = "'GetChannelParserBase' is a base class and should not be instantiated directly."
            raise TypeError(msg)

        self.int_parser = int_parser or builtins_parsers.IntParser.default(int)
        self.allow_api_requests = allow_api_requests

    async def loads(self, argument: str, /) -> _ChannelT:
        """Load a channel from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a channel.

            This always matches the channel type of the parser.

        Raises
        ------
        :class:`LookupError`:
            A channel with the id stored in the ``argument`` could not be found.
        :class:`TypeError`:
            A channel with the id stored in the ``argument`` was found, but it
            was of an incorrect channel type.

        """
        channel_id = await self.int_parser.loads(argument)

        maybe_channel = (
            di.resolve_dependency(disnake.abc.GuildChannel, None)
            or di.resolve_dependency(disnake.Thread, None)
            or di.resolve_dependency(disnake.abc.PrivateChannel, None)
        )
        if maybe_channel and isinstance(maybe_channel, self.parser_type):
            return maybe_channel

        maybe_guild = di.resolve_dependency(disnake.Guild, None)
        if maybe_guild:
            maybe_channel = maybe_guild.get_channel(channel_id)
            if maybe_channel and isinstance(maybe_channel, self.parser_type):
                return maybe_channel

        maybe_client = di.resolve_dependency(disnake.Client, None)
        if maybe_client:
            maybe_channel = maybe_client.get_channel(channel_id)
            if maybe_channel and isinstance(maybe_channel, self.parser_type):
                return maybe_channel

            if self.allow_api_requests:
                with contextlib.suppress(disnake.HTTPException):
                    maybe_channel = await maybe_client.fetch_channel(channel_id)

                if isinstance(maybe_channel, self.parser_type):
                    return maybe_channel

        if maybe_channel is None:
            msg = f"Could not find a channel with id {argument!r}."
            raise LookupError(msg)

        msg = (
            f"Found a channel of type {type(maybe_channel).__name__!r} for id"
            f" {argument!r}, expected type {self.parser_type.__name__!r}."
        )
        raise TypeError(msg)

    async def dumps(self, argument: _ChannelT, /) -> str:
        """Dump a channel into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return await self.int_parser.dumps(argument.id)


# ABSTRACT


@parser_base.register_parser_for(disnake.abc.GuildChannel)
@attrs.define(slots=True)
class GuildChannelParser(ChannelParserBase[disnake.abc.GuildChannel]):
    r"""Parser type with support for guild channels.

    .. warning::
        This parser can make API requests.

    Parameters
    ----------
    int_parser:
        The :class:`~disnake_compass.impl.parser.builtins.IntParser` to use
        internally for this parser.

    """

    parser_type = disnake.abc.GuildChannel


@parser_base.register_parser_for(disnake.abc.PrivateChannel)
@attrs.define(slots=True)
class PrivateChannelParser(ChannelParserBase[disnake.abc.PrivateChannel]):
    r"""Parser type with support for private channels.

    .. warning::
        This parser can make API requests.

    Parameters
    ----------
    int_parser:
        The :class:`~disnake_compass.impl.parser.builtins.IntParser` to use
        internally for this parser.

    """

    parser_type = disnake.abc.PrivateChannel  # pyright: ignore[reportAssignmentType]


# ASYNC PRIVATE


@parser_base.register_parser_for(disnake.DMChannel)
@attrs.define(slots=True)
class DMChannelParser(ChannelParserBase[disnake.DMChannel]):
    r"""Parser type with support for DM channels.

    .. warning::
        This parser can make API requests.

    Parameters
    ----------
    int_parser:
        The :class:`~disnake_compass.impl.parser.builtins.IntParser` to use
        internally for this parser.

    """

    parser_type = disnake.DMChannel


@parser_base.register_parser_for(disnake.GroupChannel)
@attrs.define(slots=True)
class GroupChannelParser(ChannelParserBase[disnake.GroupChannel]):
    r"""Parser type with support for group channels.

    .. warning::
        This parser can make API requests.

    Parameters
    ----------
    int_parser:
        The :class:`~disnake_compass.impl.parser.builtins.IntParser` to use
        internally for this parser.

    """

    parser_type = disnake.GroupChannel


# ASYNC GUILD


@parser_base.register_parser_for(disnake.ForumChannel)
@attrs.define(slots=True)
class ForumChannelParser(ChannelParserBase[disnake.ForumChannel]):
    r"""Parser type with support for forum channels.

    .. warning::
        This parser can make API requests.

    Parameters
    ----------
    int_parser:
        The :class:`~disnake_compass.impl.parser.builtins.IntParser` to use
        internally for this parser.

    """

    parser_type = disnake.ForumChannel


@parser_base.register_parser_for(disnake.NewsChannel)
@attrs.define(slots=True)
class NewsChannelParser(ChannelParserBase[disnake.NewsChannel]):
    r"""Parser type with support for news channels.

    .. warning::
        This parser can make API requests.

    Parameters
    ----------
    int_parser:
        The :class:`~disnake_compass.impl.parser.builtins.IntParser` to use
        internally for this parser.

    """

    parser_type = disnake.NewsChannel


@parser_base.register_parser_for(disnake.VoiceChannel)
@attrs.define(slots=True)
class VoiceChannelParser(ChannelParserBase[disnake.VoiceChannel]):
    r"""Parser type with support for voice channels.

    .. warning::
        This parser can make API requests.

    Parameters
    ----------
    int_parser:
        The :class:`~disnake_compass.impl.parser.builtins.IntParser` to use
        internally for this parser.

    """

    parser_type = disnake.VoiceChannel


@parser_base.register_parser_for(disnake.StageChannel)
@attrs.define(slots=True)
class StageChannelParser(ChannelParserBase[disnake.StageChannel]):
    r"""Parser type with support for stage channels.

    .. warning::
        This parser can make API requests.

    Parameters
    ----------
    int_parser:
        The :class:`~disnake_compass.impl.parser.builtins.IntParser` to use
        internally for this parser.

    """

    parser_type = disnake.StageChannel


@parser_base.register_parser_for(disnake.TextChannel)
@attrs.define(slots=True)
class TextChannelParser(ChannelParserBase[disnake.TextChannel]):
    r"""Parser type with support for text channels.

    .. warning::
        This parser can make API requests.

    Parameters
    ----------
    int_parser:
        The :class:`~disnake_compass.impl.parser.builtins.IntParser` to use
        internally for this parser.

    """

    parser_type = disnake.TextChannel


@parser_base.register_parser_for(disnake.Thread)
@attrs.define(slots=True)
class ThreadParser(ChannelParserBase[disnake.Thread]):
    r"""Parser type with support for threads.

    .. warning::
        This parser can make API requests.

    Parameters
    ----------
    int_parser:
        The :class:`~disnake_compass.impl.parser.builtins.IntParser` to use
        internally for this parser.

    """

    parser_type = disnake.Thread


@parser_base.register_parser_for(disnake.CategoryChannel)
@attrs.define(slots=True)
class CategoryParser(ChannelParserBase[disnake.CategoryChannel]):
    r"""Parser type with support for categories.

    .. warning::
        This parser can make API requests.

    Parameters
    ----------
    int_parser:
        The :class:`~disnake_compass.impl.parser.builtins.IntParser` to use
        internally for this parser.

    """

    parser_type = disnake.CategoryChannel


@parser_base.register_parser_for(disnake.PartialMessageable)
@attrs.define(slots=True)
class PartialMessageableParser(parser_base.Parser[disnake.PartialMessageable]):
    r"""Parser type with support for partial messageables.

    Parameters
    ----------
    channel_type:
        The channel type to use for :class:`disnake.PartialMessageable`\s
        created by this class.

        Defaults to ``None``.
    int_parser:
        The :class:`~disnake_compass.impl.parser.builtins.IntParser` to use
        internally for this parser.

    """

    channel_type: disnake.ChannelType | None
    r"""The channel type to use for :class:`disnake.PartialMessageable`\s
    created by this class.

    This determines which operations are valid on the partial messageables.
    """
    int_parser: builtins_parsers.IntParser = attrs.field(
        factory=lambda: builtins_parsers.IntParser.default(int),
    )
    """The :class:`~disnake_compass.impl.parser.builtins.IntParser` to use
    internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default channel parser will also return compressed results.
    """

    async def loads(self, argument: str, /) -> disnake.PartialMessageable:
        """Load a partial messageable from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a channel.

            This always matches the channel type of the parser.

        """
        client = di.resolve_dependency(disnake.Client)
        return client.get_partial_messageable(int(argument), type=self.channel_type)

    async def dumps(self, argument: disnake.PartialMessageable, /) -> str:
        """Dump a partial messageable into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return await self.int_parser.dumps(argument.id)
