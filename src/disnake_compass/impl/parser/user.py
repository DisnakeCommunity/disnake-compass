"""Parser implementations for disnake user types."""

from __future__ import annotations

import contextlib
import typing

import attrs
import disnake

from disnake_compass.impl.parser import base as parser_base
from disnake_compass.impl.parser import builtins as builtins_parsers
from disnake_compass.internal import di

__all__: typing.Sequence[str] = ("MemberParser", "UserParser")


@parser_base.register_parser_for(disnake.User)
@attrs.define(slots=True)
class UserParser(parser_base.Parser[disnake.User]):
    r"""Parser type with support for users.

    .. warning::
        This parser can make API requests.

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
    default guild parser will also return compressed results.
    """
    allow_api_requests: bool = attrs.field(default=True, kw_only=True)
    """Whether or not to allow this parser to make API requests.

    Parsers will always try getting a result from cache first.
    """

    async def loads(self, argument: str, /) -> disnake.User:
        """Load a user from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a user.

        Raises
        ------
        :class:`LookupError`:
            A user with the id stored in the ``argument`` could not be found.

        """
        user_id = await self.int_parser.loads(argument)

        maybe_author = di.resolve_dependency(disnake.member._UserTag, None)  # pyright: ignore[reportPrivateUsage, reportPrivateImportUsage]  # noqa: SLF001
        if maybe_author and maybe_author.id == user_id:
            if isinstance(maybe_author, disnake.User):
                return maybe_author
            if isinstance(maybe_author, disnake.Member):
                return maybe_author._user  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001

        maybe_client = di.resolve_dependency(disnake.Client, None)
        if maybe_client:
            user = maybe_client.get_user(user_id)
            if user:
                return user

            if self.allow_api_requests:
                with contextlib.suppress(disnake.HTTPException):
                    return await maybe_client.fetch_user(user_id)

        msg = f"Could not find a user with id {argument!r}."
        raise LookupError(msg)

    async def dumps(self, argument: disnake.User, /) -> str:
        """Dump a user into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return await self.int_parser.dumps(argument.id)


@parser_base.register_parser_for(disnake.Member)
@attrs.define(slots=True)
class MemberParser(parser_base.Parser[disnake.Member]):
    r"""Asynchronous parser type with support for members.

    .. warning::
        This parser can make API requests.

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
    default guild parser will also return compressed results.
    """
    allow_api_requests: bool = attrs.field(default=True, kw_only=True)
    """Whether or not to allow this parser to make API requests.

    Parsers will always try getting a result from cache first.
    """

    async def loads(self, argument: str, /) -> disnake.Member:
        """Load a member from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a member.

        Raises
        ------
        :class:`LookupError`:
            A member with the id stored in the ``argument`` could not be found.

        """
        member_id = await self.int_parser.loads(argument)

        maybe_member = di.resolve_dependency(disnake.Member, None)
        if maybe_member and maybe_member.id == member_id:
            return maybe_member

        guild = di.resolve_dependency(disnake.Guild)
        member = guild.get_member(member_id)
        if member:
            return member

        if self.allow_api_requests:
            with contextlib.suppress(disnake.HTTPException):
                return await guild.fetch_member(member_id)

        msg = f"Could not find a member with id {argument!r}."
        raise LookupError(msg)

    async def dumps(self, argument: disnake.Member, /) -> str:
        """Dump a user into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return await self.int_parser.dumps(argument.id)
