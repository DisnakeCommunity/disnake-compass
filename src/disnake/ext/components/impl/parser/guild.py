"""Parser implementations for disnake.Guild type."""

from __future__ import annotations

import contextlib
import typing

import disnake
from disnake.ext.components.impl.parser import base as parser_base
from disnake.ext.components.impl.parser import builtins as builtins_parsers

__all__: typing.Sequence[str] = (
    "GuildParser",
    "InviteParser",
    "RoleParser",
)


@parser_base.register_parser_for(disnake.Guild)
class GuildParser(parser_base.Parser[disnake.Guild]):
    """Parser type with support for guilds.

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
    default guild parser will also return compressed results.
    """
    allow_api_requests: bool
    """Whether or not to allow this parser to make API requests.

    Parsers will always try getting a result from cache first.
    """

    def __init__(
        self,
        int_parser: typing.Optional[builtins_parsers.IntParser] = None,
        *,
        allow_api_requests: bool = True,
    ) -> None:
        self.int_parser = int_parser or builtins_parsers.IntParser.default(int)
        self.allow_api_requests = allow_api_requests

    async def loads(
        self,
        argument: str,
        /,
        *,
        maybe_guild: typing.Optional[disnake.Guild] = parser_base.inject(disnake.Guild, None),
        maybe_client: typing.Optional[disnake.Client] = parser_base.inject(disnake.Client, None),
    ) -> disnake.Guild:
        """Load a guild from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a guild.

        Raises
        ------
        :class:`LookupError`:
            A guild with the id stored in the ``argument`` could not be found.

        """
        guild_id = await self.int_parser.loads(argument)

        if maybe_guild and maybe_guild.id == guild_id:
            return maybe_guild

        if maybe_client:
            maybe_guild = maybe_client.get_guild(guild_id)
            if maybe_guild:
                return maybe_guild

            if self.allow_api_requests:
                with contextlib.suppress(disnake.HTTPException):
                    return await maybe_client.fetch_guild(guild_id)

        msg = f"Could not find a guild with id {argument!r}."
        raise LookupError(msg)

    async def dumps(self, argument: disnake.Guild) -> str:
        """Dump a guild into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return await self.int_parser.dumps(argument.id)

@parser_base.register_parser_for(disnake.Invite)
class InviteParser(parser_base.Parser[disnake.Invite]):
    """Asynchronous parser type with support for guilds.

    .. warning::
        This parser can make API requests.

    Parameters
    ----------
    with_counts:
        Whether to include count information in the invite.
    with_expiration:
        Whether to include the expiration date of the invite.
    guild_scheduled_event_id: :class:`int`
        The ID of the scheduled event to include in the invite.

        If not provided, defaults to the ``event`` parameter in the URL if
        it exists, or the ID of the scheduled event contained in the
        provided invite object.

    """

    with_counts: bool
    """Whether to include the number of times an invite was used."""
    with_expiration: bool
    """Whether to include when the invite expires."""
    guild_scheduled_event_id: typing.Optional[int]
    """The ID of the scheduled event to include in the invite."""

    def __init__(
        self,
        *,
        with_counts: bool = True,
        with_expiration: bool = True,
        guild_scheduled_event_id: typing.Optional[int] = None,
    ) -> None:
        self.with_counts = with_counts
        self.with_expiration = with_expiration
        self.guild_scheduled_event_id = guild_scheduled_event_id

    async def loads(
        self,
        argument: str,
        /,
        *,
        client: disnake.Client = parser_base.inject(disnake.Client),
    ) -> disnake.Invite:
        """Asynchronously load a guild invite from a string.

        This uses the underlying :attr:`int_parser`.

        This method first tries to get the invite from cache. If this fails,
        it will try to fetch the invite instead.

        .. warning::
            This method can make API requests.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a guild invite.
        source:
            The source to use for parsing.

            Must be a type that has access to a
            :class:`bot <disnake.ext.commands.Bot>` attribute.

        """
        return await client.fetch_invite(
            argument,
            with_counts=self.with_counts,
            with_expiration=self.with_expiration,
            guild_scheduled_event_id=self.guild_scheduled_event_id,
        )

    async def dumps(self, argument: disnake.Invite, /) -> str:
        """Dump a guild invite into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return argument.id


@parser_base.register_parser_for(disnake.Role)
class RoleParser(parser_base.Parser[disnake.Role]):
    r"""Synchronous parser type with support for roles.

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
    default role parser will also return compressed results.
    """
    allow_api_requests: bool
    """Whether or not to allow this parser to make API requests.

    Parsers will always try getting a result from cache first.
    """

    def __init__(
        self,
        int_parser: typing.Optional[builtins_parsers.IntParser] = None,
        *,
        allow_api_requests: bool = True,
    ) -> None:
        self.int_parser = int_parser or builtins_parsers.IntParser.default(int)
        self.allow_api_requests = allow_api_requests

    async def loads(
        self,
        argument: str,
        /,
        *,
        guild: disnake.Guild = parser_base.inject(disnake.Guild),
    ) -> disnake.Role:
        """Load a role from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a role.
        source:
            The source to use for parsing.

            Must be a type that has access to a
            :class:`guild <disnake.Guild>`, :class:`message <disnake.Message>`,
            or a :class:`channel <disnake.TextChannel>` attribute.

        Raises
        ------
        :class:`LookupError`:
            A role with the id stored in the ``argument`` could not be found.

        """
        role_id = await self.int_parser.loads(argument)

        role = guild.get_role(role_id)
        if role:
            return role

        if self.allow_api_requests:
            with contextlib.suppress(disnake.HTTPException):
                for role in await guild.fetch_roles():
                    if role.id == role_id:
                        return role

        msg = f"Could not find a role with id {argument!r}."
        raise LookupError(msg)

    async def dumps(self, argument: disnake.Role) -> str:
        """Dump a role into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return await self.int_parser.dumps(argument.id)
