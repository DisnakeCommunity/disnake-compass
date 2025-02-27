"""Parser implementations for standard library and disnake enums and flags."""

import enum
import typing

import attrs
import disnake

from disnake_compass.api import parser as parser_api
from disnake_compass.impl.parser import base as parser_base

__all__: typing.Sequence[str] = ("EnumParser", "FlagParser")

_AnyEnum: typing.TypeAlias = enum.Enum | disnake.Enum | disnake.flags.BaseFlags
_EnumT = typing.TypeVar("_EnumT", bound=_AnyEnum)


def _get_enum_type(enum_class: type[_AnyEnum]) -> type | None:
    if issubclass(enum_class, disnake.flags.BaseFlags):
        return int

    maybe_type: type = getattr(enum_class, "_member_type_", object)
    if maybe_type is not object:
        return maybe_type

    # Get first member's type
    member_iter = iter(enum_class)
    maybe_type = typing.cast(  # python typing sucks.
        type[typing.Any],
        type(next(member_iter).value),
    )

    # TODO: Check if this can be `is` instead of `==`.
    # If all members match this type, return it.
    if all(type(member.value) == maybe_type for member in member_iter):  # noqa: E721
        return maybe_type

    # No single type; store by name instead.
    return None


@parser_base.register_parser_for(
    enum.Enum,
    disnake.Enum,
    enum.Flag,
    disnake.flags.BaseFlags,
    priority=20,
)
@attrs.define(slots=True, init=False)
class EnumParser(parser_base.Parser[_EnumT]):
    """Parser type for enums and flags.

    Enums and flags are stored by value instead of by name. This makes parsing
    a bit slower, but values are generally shorter than names.

    This parser type works for standard library and disnake enums and flags.
    Note that this only works for enums and flags where all values are of the
    same type.

    Parameters
    ----------
    enum_class:
        The enum or flag class to use for parsing.
    store_by_value:
        Whether :meth:`loads` and :meth:`dumps` expect the enum value type or a string.

        For enum types where the members are *not* all of the same type, this
        *must* be ``False``.

        For enum types where all members are integers, this defaults to
        ``True``, otherwise this defaults to ``False``.

    """

    enum_class: type[_EnumT]
    """The enum or flag class to use for parsing."""
    store_by_value: bool
    """Whether :meth:`loads` and :meth:`dumps` expect the enum's value type or a string.

    For enum types where the members are *not* all of the same type, this
    *must* be ``False``.
    """
    value_parser: parser_api.Parser[typing.Any]
    """The parser responsible for converting to/from the enum type.

    If :attr:`store_by_values` is set to ``False``, this is *always* a
    :class:`~disnake_compass.parser.StringParser`.
    """

    def __init__(
        self,
        enum_class: type[_EnumT],
        *,
        store_by_value: bool | None = None,
    ) -> None:
        if issubclass(enum_class, disnake.flags.BaseFlags) and store_by_value is False:
            msg = "Cannot store disnake flags by name, as their members do not have names."
            raise ValueError(msg)

        value_type = _get_enum_type(enum_class)

        # If the enum is not of a single type and store_by_value wasn't
        # explicitly set or was explicitly set to false, parse by name.
        if value_type is None and not store_by_value:
            self.store_by_value = False
            value_type = str

        # If the value type could be determined, set it on the parser and
        # respect the input for store_by_value-- default to True for integers.
        elif value_type is not None:
            self.store_by_value = (
                issubclass(value_type, int)
                if store_by_value is None
                else store_by_value
            )  # fmt: skip

        # If the value type could not be determined but the user explicitly set
        # store_by_value to True, raise an exception.
        else:
            msg = (
                "Cannot store enum members by value for enums with members of"
                " varying types. Please either set `store_by_value` to False"
                " or make sure all enum members are of the same type."
            )
            raise ValueError(msg)

        self.enum_class = enum_class
        self.value_parser = parser_base.get_parser(value_type)

    async def loads(self, argument: str, /) -> _EnumT:
        """Load an enum member from a string.

        This uses the underlying :attr:`value_parser`.

        .. note::
            If :attr:`store_by_value` is True, the ``argument`` is expected to
            be the value of an enum member; otherwise, the ``argument`` is
            expted to be the name.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a channel.

            This always matches the channel type of the parser.

        """
        parsed = await self.value_parser.loads(argument)

        if self.store_by_value:
            return self.enum_class(parsed)  # pyright: ignore[reportCallIssue]
        return self.enum_class[parsed]  # pyright: ignore[reportInvalidTypeArguments]

    async def dumps(self, argument: _EnumT) -> str:
        """Dump an enum member into a string.

        .. note::
            If :attr:`store_by_value` is True, this dumps the name of the
            enum member passed as ``argument``; otherwise, this dumps its
            value.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        if self.store_by_value:
            return await self.value_parser.dumps(argument.value)
        # Baseflags members are always integers. This should never error
        # due to the check in __init__.
        assert not isinstance(argument, disnake.flags.BaseFlags)
        return await self.value_parser.dumps(argument.name)


FlagParser = EnumParser
