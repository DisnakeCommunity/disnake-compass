"""Implementation of parser base classes upon which actual parsers are built."""

from __future__ import annotations

import typing

import attrs

from disnake_compass.api import parser as parser_api

if typing.TYPE_CHECKING:
    import typing_extensions

__all__: typing.Sequence[str] = (
    "Parser",
    "get_parser",
    "register_parser",
)

ParserT = typing.TypeVar("ParserT", bound=parser_api.Parser)

_PARSERS: dict[type, type[parser_api.Parser[typing.Any]]] = {}
_REV_PARSERS: dict[
    type[parser_api.Parser[typing.Any]],
    tuple[type, ...],
] = {}
_PARSER_PRIORITY: dict[type[parser_api.Parser[typing.Any]], int] = {}


def _issubclass(
    cls: type,
    class_or_tuple: type | tuple[type, ...],
) -> bool:
    try:
        return issubclass(cls, class_or_tuple)

    except TypeError:
        if isinstance(class_or_tuple, tuple):
            return any(cls is cls_ for cls_ in class_or_tuple)

        return cls is class_or_tuple


def register_parser(
    parser: type[parser_api.Parser[parser_api.ParserType]],
    *types: type[parser_api.ParserType],
    priority: int = 0,
    force: bool = True,
) -> None:
    """Register a parser class as the default parser for the provided type.

    The default parser will automatically be used for any field annotated
    with that type. For example, the default parser for integers is
    :class:`disnake_compass.IntParser`, an instance of which will automatically be
    assigned to any custom id fields annotated with `int`.

    Parameters
    ----------
    parser:
        The parser to register.
    *types:
        The types for which to register the provided parser as the default.
    priority:
        When a type has multiple parsers registered to it, priority is used to
        determine which parser to use.
    force:
        Whether or not to overwrite existing defaults. Defaults to ``True``.

    """
    # This allows e.g. is_default_for=(Tuple[Any, ...],) so pyright doesn't complain.
    # The stored type will then still be tuple, as intended.
    types = tuple(typing.get_origin(type_) or type_ for type_ in types)
    setter = dict.__setitem__ if force else dict.setdefault  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

    setter(_REV_PARSERS, parser, types)
    setter(_PARSER_PRIORITY, parser, priority)
    for type_ in types:
        setter(_PARSERS, type_, parser)


def register_parser_for(
    *is_default_for: type[typing.Any],
    priority: int = 0,
) -> typing.Callable[[type[ParserT]], type[ParserT]]:
    def wrapper(cls: type[ParserT]) -> type[ParserT]:
        register_parser(cls, *is_default_for, priority=priority)
        return cls

    return wrapper


def _get_parser_type(
    type_: type[parser_api.ParserType],
) -> type[parser_api.Parser[parser_api.ParserType]]:
    # Fast lookup...
    if type_ in _PARSERS:
        return _PARSERS[type_]

    # Slow lookup for subclasses of existing types...
    best_entry = max(
        (entry for entry, parser_types in _REV_PARSERS.items() if _issubclass(type_, parser_types)),
        default=None,
        key=_PARSER_PRIORITY.__getitem__,
    )
    if best_entry is not None:
        return best_entry

    message = f"No parser available for type {type_.__name__!r}."
    raise TypeError(message)


# TODO: Maybe cache this?
def get_parser(  # noqa: D417
    type_: type[parser_api.ParserType],
) -> parser_api.Parser[parser_api.ParserType]:
    r"""Get the default parser for the provided type.

    Note that type annotations such as ``Union[int, str]`` are also valid.

    Parameters
    ----------
    type\_:
        The type for which to return the default parser.

    Returns
    -------
    :class:`Parser`\[``_T``]:
        The default parser for the provided type.

    Raises
    ------
    :class:`TypeError`:
        Could not create a parser for the provided type.

    """
    # TODO: Somehow allow more flexibility here. It would at the very least
    #       be neat to be able to pick between strictly sync/async parsers
    #       (mainly for the purpose of not making api requests); but perhaps
    #       allowing the user to pass a filter function could be cool?
    origin = typing.get_origin(type_)
    return _get_parser_type(origin or type_).default(type_)


@typing.runtime_checkable
@attrs.define(slots=True)
class Parser(
    parser_api.Parser[parser_api.ParserType],
    typing.Protocol[parser_api.ParserType],
):
    """Class that handles parsing of one custom id field to and from a desired type.

    A parser contains two main methods, :meth:`loads` and :meth:`dumps`.
    ``loads``, like :func:`json.loads` serves to turn a string value into
    a different type. Similarly, ``dumps`` serves to convert that type
    back into a string.
    """

    @classmethod
    def default(  # noqa: D102
        cls,
        target_type: type[parser_api.ParserType],  # noqa: ARG003
        /,
    ) -> typing_extensions.Self:
        # <<Docstring inherited from parser_api.Parser>>
        return cls()

    @classmethod
    def default_types(cls) -> tuple[type, ...]:
        """Return the types for which this parser type is the default implementation.

        Returns
        -------
        Sequence[type]:
            The types for which this parser type is the default implementation.

        """
        return _REV_PARSERS[cls]

    async def loads(self, argument: typing.Any, /) -> parser_api.ParserType:  # noqa: D102, ANN401
        # <<Docstring inherited from parser_api.Parser>>
        ...

    async def dumps(self, argument: parser_api.ParserType, /) -> str:  # noqa: D102
        # <<Docstring inherited from parser_api.Parser>>
        ...
