"""Parser implementations for (mostly) builtin types."""

from __future__ import annotations

import contextlib
import inspect
import string
import typing

import attrs
import typing_extensions

from disnake_compass.impl.parser import base as parser_base

if typing.TYPE_CHECKING:
    from disnake_compass.api import parser as parser_api

__all__: typing.Sequence[str] = (
    "BoolParser",
    "CollectionParser",
    "FloatParser",
    "IntParser",
    "StringParser",
    "TupleParser",
    "UnionParser",
)

_NoneType: type[None] = type(None)
_NONES = (None, _NoneType)
_INT_CHARS = string.digits + string.ascii_lowercase

_CollectionT = typing_extensions.TypeVar(  # Simplest iterable container object.
    "_CollectionT",
    bound=typing.Collection[object],
    default=typing.Collection[str],
)
_TupleT = typing_extensions.TypeVar("_TupleT", bound=tuple[typing.Any, ...])
_T = typing_extensions.TypeVar("_T")

# NONE


@parser_base.register_parser_for(_NoneType)
@attrs.define(slots=True)
class NoneParser(parser_base.Parser[None]):
    r"""Parser implementation for :obj:`None`.

    Mainly relevant for :obj:`~typing.Optional`\[...] parsers.

    Parameters
    ----------
    strict: bool
        Whether this parser should be set to :attr:`strict` mode.

        To prevent unforeseen bugs, this defaults to :obj:`True`.

    """

    strict: bool = attrs.field(default=True, kw_only=True)
    """Whether this parser is set to strict mode.

    See :meth:`loads` and :meth:`dumps` for the implications of strict-mode.
    """

    async def loads(self, argument: str, /) -> None:
        """Load ``None`` from a string.

        If :attr:`strict` is set to ``True``, this will fail if the
        provided ``argument`` isn't the empty string (``""``). Otherwise,
        this parser will *always* return ``None``.

        Parameters
        ----------
        argument:
            The string that is to be converted to ``None``.

        Raises
        ------
        ValueError:
            The parser is in strict mode, and the provided ``argument`` was not
            the empty string.

        """
        if not argument or not self.strict:
            return None  # noqa: RET501

        msg = f"Strict `NoneParser`s can only load the empty string, got {argument!r}."
        raise ValueError(msg)

    async def dumps(self, argument: None, /) -> str:
        """Dump ``None`` into a string.

        If :attr:`strict` is set to ``True``, this will fail if the
        provided ``argument`` isn't exactly ``None``. Otherwise,
        this parser will *always* return ``None``.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        Raises
        ------
        ValueError:
            The parser is in strict mode, and the provided ``argument`` was not
            ``None``.

        """
        if argument is None or not self.strict:
            return ""

        msg = f"Strict `NoneParser`s can only dump `None`, got {argument!r}."
        raise ValueError(msg)


# INT / FLOAT


def _removesuffix(string: str, suffix: str) -> str:
    return string[: -len(suffix) if string.endswith(suffix) else None]


def dumps_float(number: float) -> str:
    """Dump a float to a string.

    Ensures trailing .0 are stripped to minimise float character length.
    """
    return _removesuffix(str(number), ".0")


# TODO: decimal.Decimal parser for decimal numbers with set precision?


@parser_base.register_parser_for(float)
@attrs.define(slots=True)
class FloatParser(parser_base.Parser[float]):
    r"""Parser implementation for :class:`float`\s."""

    async def loads(self, argument: str, /) -> float:
        """Load a floating point number from a string.

        Parameters
        ----------
        argument:
            The value that is to be loaded into a floating point number.

        """
        return float(argument)

    async def dumps(self, argument: float, /) -> str:
        """Dump a floating point number into a string.

        Strips trailing ".0" where possible.

        Parameters
        ----------
        argument:
            The string that is to be converted into a floating point number.

        """
        return dumps_float(argument)


def _validate_base(_instance: object, _attribute: object, base: int) -> None:
    if not 2 <= base <= 36:  # noqa: PLR2004
        msg = "Base must be between 2 and 36."
        raise ValueError(msg)


@parser_base.register_parser_for(int)
@attrs.define(slots=True)
class IntParser(parser_base.Parser[int]):
    r"""Parser implementation for :class:`int`\s.

    Parameters
    ----------
    signed:
        Whether the parser supports signed integers.
        Defaults to ``True``.
    base:
        The base to use to use for storing integers.
        This is limited to ``2 <= base <= 36``.
        Defaults to ``36``.

    """

    signed: bool = attrs.field(default=True)
    """Whether the parser supports signed integers."""
    base: int = attrs.field(default=36, validator=_validate_base)
    """The base to use to use for storing integers.
    This is limited to ``2 <= base <= 36`` as this is the range supported by
    python's :class:`int` constructor.

    If a greater base is required, a custom integer parser will have to be
    implemented.
    """

    async def loads(self, argument: str, /) -> int:
        r"""Load an integer from a string.

        Parameters
        ----------
        argument:
            The string that is to be converted to an ``int``.

        Raises
        ------
        ValueError:
            The parser has :attr:`signed` set to ``False`` but the argument
            was a negative number.
            Alternatively, the provided argument is not a valid integer at all.

        """
        result = int(argument, self.base)
        if not self.signed and result < 0:
            msg = "Unsigned numbers cannot be < 0."
            raise ValueError(msg)

        return result

    async def dumps(self, argument: int, /) -> str:
        """Dump an integer into a string.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        # Try to short-circuit as much as possible
        if argument < self.base:
            return str(argument)
        if self.base == 2:  # noqa: PLR2004
            return f"{argument:b}"
        if self.base == 8:  # noqa: PLR2004
            return f"{argument:o}"
        if self.base == 10:  # noqa: PLR2004
            return str(argument)
        if self.base == 16:  # noqa: PLR2004
            return f"{argument:x}"

        # Can't short-circuit, convert to string manually.
        digits: list[int] = []
        while argument:
            digits.append(argument % self.base)
            argument //= self.base

        return "".join(_INT_CHARS[d] for d in reversed(digits))


# BOOL

_DEFAULT_TRUES = frozenset(["true", "t", "yes", "y", "1"])
_DEFAULT_FALSES = frozenset(["false", "f", "no", "n", "0"])


@parser_base.register_parser_for(bool)
@attrs.define(slots=True)
class BoolParser(parser_base.Parser[bool]):
    """Parser type with support for bools.

    This parser type can be supplied with a collection of strings for the
    values that should be considered true and false. By default,
    ``"true", "t", "yes", "y", "1"`` are considered ``True``, while
    ``"false", "f", "no", "n", "0"`` are considered ``False``. Note that this
    is case-insensitive.

    Parameters
    ----------
    trues:
        Values that should be considered ``True`` by this parser.
    falses:
        Values that should be considered ``False`` by this parser.

    """

    trues: typing.Collection[str] = attrs.field(factory=_DEFAULT_TRUES.copy)
    """A collection of values that should be considered ``True`` by this parser."""
    falses: typing.Collection[str] = attrs.field(factory=_DEFAULT_FALSES.copy)
    """A collection of values that should be considered ``False`` by this parser."""

    async def loads(self, argument: str, /) -> bool:
        """Load a boolean from a string.

        Parameters
        ----------
        argument:
            The string that is to be converted into a boolean.

        Raises
        ------
        ValueError:
            The string is not in :attr:`trues` or :attr:`falses`.

        """
        if argument in self.trues:
            return True
        if argument in self.falses:
            return False

        trues_str = ", ".join(map(repr, self.trues))
        falses_str = ", ".join(map(repr, self.falses))
        msg = (
            f"Failed to parse {argument!r} into a bool. Expected any of"
            f" {trues_str} for True, or any of {falses_str} for False."
        )
        raise ValueError(msg)

    async def dumps(self, argument: bool, /) -> str:  # noqa: FBT001
        """Dump a boolean into a string.

        By default, this opts to dump as ``"1"`` for ``True`` or ``"0"`` for
        ``False`` to only use one character's worth of space from the custom id.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return "1" if argument else "0"


# STRING


@parser_base.register_parser_for(str)
@attrs.define(slots=True)
class StringParser(parser_base.Parser[str]):
    """Parser type with support for strings.

    Both loads and dumps are essentially no-ops.
    """

    async def loads(self, argument: str, /) -> str:
        """Load a string from a string.

        Parameters
        ----------
        argument:
            The string that is to be converted into a string.

        """
        return argument

    async def dumps(self, argument: str, /) -> str:
        """Dump a string into a string.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return argument


def _resolve_collection(type_: type[_CollectionT]) -> type[_CollectionT]:
    # ContainerParser itself does not support tuples.
    if issubclass(type_, tuple):
        msg = (
            f"{CollectionParser.__name__}s do not support tuples. Please use a "
            f"{TupleParser.__name__} instead."
        )
        raise TypeError(msg)

    if not typing_extensions.is_protocol(type_) and not inspect.isabstract(type_):
        # Concrete type, return as-is.
        return type_

    # Try to resolve an abstract type to a valid concrete structural subtype.
    if issubclass(type_, typing.Sequence):
        return typing.cast(type[_CollectionT], list)

    if issubclass(type_, typing.AbstractSet):
        return typing.cast(type[_CollectionT], set)

    msg = f"Cannot infer a concrete type for abstract type {type_.__name__!r}."
    raise TypeError(msg)


# NOTE: TupleParser *must* be registered before CollectionParser!


@parser_base.register_parser_for(tuple, priority=10)
@attrs.define(slots=True, init=False)
class TupleParser(parser_base.Parser[_TupleT]):
    r"""Parser type with support for :class:`tuple`\s.

    The benefit of a tuple parser is fixed-length checks and the ability to set
    multiple types. For example, a ``Tuple[str, int, bool]`` parser will
    actually return a tuple with a ``str``, ``int``, and ``bool`` inside.

    Parameters
    ----------
    *inner_parsers:
        The parsers to use to parse the items inside the tuple.

        Defaults to a single string parser, i.e. a one-element tuple containing
        exactly one string.
    sep:
        The separator to use.

        Defaults to ",".

    """

    inner_parsers: tuple[parser_api.Parser[typing.Any], ...]
    """The parsers to use to parse the items inside the tuple.

    These define the inner types and the allowed number of items in the in the
    tuple.
    """
    sep: str
    """The separator to use.

    Can be any string, though a single character is recommended.

    .. warning::
        Ensure that this does **not** match
        :attr:`ComponentManager.sep <disnake_compass.impl.manager.ComponentManager.sep>`
        on the component manager that corresponds to this parser's component.
        """
    tuple_cls: type[_TupleT]
    """The tuple type to use.

    This mainly exists to support NamedTuples.
    """
    # NOTE: NamedTuple does not show up in the class MRO so get_parser cannot
    #       tell the difference. NamedTuple initialisation is different from
    #       normal tuple initialisation, so we need to special-case it.

    def __init__(
        self,
        *inner_parsers: parser_api.Parser[typing.Any],
        sep: str = ",",
        tuple_cls: type[_TupleT] = tuple,
    ) -> None:
        self.inner_parsers = inner_parsers or (StringParser.default(str),)
        self.sep = sep
        self.tuple_cls = tuple_cls

    @classmethod
    def default(cls, type_: type[_TupleT], /) -> typing_extensions.Self:  # noqa: D102
        if hasattr(type_, "__annotations__"):
            # This is a namedtuple.
            args = typing.get_type_hints(type_).values()
        else:
            args = typing.get_args(type_)

        inner_parsers = [parser_base.get_parser(arg) for arg in args]
        return cls(*inner_parsers, tuple_cls=type_)

    async def loads(self, argument: str, /) -> _TupleT:
        """Load a tuple from a string.

        Parameters
        ----------
        argument:
            The string that is to be converted into a tuple.

            This is split over :attr:`sep` and then each individual substring
            is passed to its respective inner parser.

        Raises
        ------
        RuntimeError:
            The number of substrings after splitting does not match the number
            of inner parsers.

        """
        parts = argument.split(self.sep)

        # NamedTuples should be instantiated using _make.
        initialiser = getattr(self.tuple_cls, "_make", self.tuple_cls)
        return initialiser(
            [
                await parser.loads(part)
                for parser, part in zip(self.inner_parsers, parts, strict=True)
            ],
        )

    async def dumps(self, argument: _TupleT, /) -> str:
        """Dump a tuple into a string.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        Raises
        ------
        :class:`RuntimeError`:
            The length of the ``argument`` tuple does not match the number of
            inner parsers.

        """
        return self.sep.join(
            [
                await parser.dumps(part)
                for parser, part in zip(self.inner_parsers, argument, strict=True)
            ],
        )


@parser_base.register_parser_for(typing.Collection)
@attrs.define(slots=True, init=False)
class CollectionParser(parser_base.Parser[_CollectionT]):
    r"""Parser type with support for :class:`typing.Collection`\s.

    This supports types such as :class:`list`, :class:`set`, etc.; but also
    abstract types such as :class:`typing.Collection` itself.

    .. note:: This parser does **not** support :class:`tuple`\s.

    Parameters
    ----------
    inner_parser:
        The parser to use to parse the items inside the collection.

        This defines the inner type for the collection.

        Defaults to a :class:`StringParser`.
    collection_type:
        The type of collection to use. This does not specify the inner type.

        Defaults to :class:`list`.
    sep:
        The separator to use.

        Can be any string, though a single character is recommended.

        Defaults to ``","``.

    """

    inner_parser: parser_api.Parser[typing.Any]
    """The parser to use to parse the items inside the collection.

    Note that, unlike a :class:`TupleParser`, a collection parser requires all
    items to be of the same type.
    """
    collection_type: type[_CollectionT]
    """The collection type for this parser.

    This is the type that holds the items, e.g. a :class:`list`.

    .. note::
        This has to support being instantiated from an iterable as
        ``collection_type(iterable_of_values)``; e.g. ``set([1,2,3])``
    """
    sep: str
    """The separator to use.

    Can be any string, though a single character is recommended.

    .. warning::
        Ensure that this does **not** match
        :attr:`ComponentManager.sep <disnake_compass.impl.manager.ComponentManager.sep>`
        on the component manager that corresponds to this parser's component.
        """

    def __init__(
        self,
        inner_parser: parser_api.Parser[typing.Any] | None = None,
        *,
        collection_type: type[_CollectionT] | None = None,
        sep: str = ",",
    ) -> None:
        self.sep = sep
        self.collection_type = typing.cast(  # Pyright do be whack sometimes.
            type[_CollectionT],
            list if collection_type is None else _resolve_collection(collection_type),
        )
        self.inner_parser = StringParser.default(str) if inner_parser is None else inner_parser

    @classmethod
    def default(  # noqa: D102
        cls,
        type_: type[_CollectionT],
        /,
    ) -> typing_extensions.Self:
        origin = typing.get_origin(type_)
        args = typing.get_args(type_)

        inner_type = next(iter(args), str)  # Get first element, default to str
        inner_parser = parser_base.get_parser(inner_type)
        return cls(inner_parser, collection_type=origin)

    async def loads(self, argument: str, /) -> _CollectionT:
        """Load a collection from a string.

        Parameters
        ----------
        argument:
            The string that is to be converted into a collection.

            This is split over :attr:`sep` and then each individual substring
            is passed to its respective inner parser.

        """
        # TODO: Maybe make this a generator instead of a list?
        parsed = [
            await self.inner_parser.loads(part)
            for part in argument.split(self.sep)
            if not part.isspace()  # TODO: Verify if this should be removed
        ]

        return self.collection_type(parsed)  # pyright: ignore[reportCallIssue]

    async def dumps(self, argument: _CollectionT, /) -> str:
        """Dump a collection into a string.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return ",".join([await self.inner_parser.dumps(part) for part in argument])


@parser_base.register_parser_for(typing.Union)  # pyright: ignore[reportArgumentType]
@attrs.define(slots=True, init=False)
class UnionParser(parser_base.Parser[_T], typing.Generic[_T]):
    r"""Parser type with support for :class:`~typing.Union`\s.

    The provided parsers are sequentially tried until one passes. If none work,
    an exception is raised instead.

    .. important::
        Unlike :class:`NoneParser`, :attr:`strict` for this class is set
        via the underlying none parser, if any. Note that this class *does*
        proxy it through the :attr:`strict` property, which supports both
        getting and setting; but **only** if this parser is :attr:`optional`.

    Parameters
    ----------
    *inner_parsers:
        The parsers with which to sequentially try to parse the argument.

        ``None`` can be provided as one of the parameters to make it optional;
        this will automatically add a **strict** :class:`NoneParser`.

    """

    inner_parsers: typing.Sequence[parser_api.Parser[typing.Any]]
    """The parsers with which to sequentially try to parse the argument."""
    optional: bool
    """Whether this parser is optional."""

    def __init__(
        self,
        *inner_parsers: parser_api.Parser[typing.Any] | None,
    ) -> None:
        if len(inner_parsers) < 2:  # noqa: PLR2004
            msg = "A Union requires two or more type arguments."
            raise TypeError(msg)

        self.optional = False
        self.inner_parsers = []
        for parser in inner_parsers:
            if parser in _NONES:
                self.optional = True

            else:
                self.inner_parsers.append(parser)

        # Ensure the NoneParser always comes last.
        if self.optional:
            self.inner_parsers.append(NoneParser.default(_NoneType))

    @classmethod
    def default(cls, type_: type[_T], /) -> typing_extensions.Self:  # noqa: D102
        args = typing.get_args(type_)

        inner_parsers = [parser_base.get_parser(arg) for arg in args]
        return cls(*inner_parsers)

    @property
    def strict(self) -> bool:
        """Whether this parser is strict.

        This is only meaningful when the parser is optional, in which case it
        directly reflects :attr:`NoneParser.strict`.
        """
        if not self.optional:
            return True

        none_parser = self.inner_parsers[-1]
        assert isinstance(none_parser, NoneParser)
        return none_parser.strict

    @strict.setter
    def strict(self, strict: bool) -> None:
        if not self.optional:
            cls = type(self).__name__
            msg = f"{cls}.strict can only be set when {cls}.optional is True."
            raise RuntimeError(msg)

        none_parser = self.inner_parsers[-1]
        assert isinstance(none_parser, NoneParser)
        none_parser.strict = strict

    async def loads(self, argument: str, /) -> _T:
        """Load a union of types from a string.

        If :attr:`optional` is ``True`` and :attr:`strict` is ``False``, this
        returns ``None`` if all parsers fail. Otherwise, an exception is raised.

        Parameters
        ----------
        argument:
            The string that is to be converted into one of the types in this union.

            Each inner parser is tried in the order they are provided, and the
            first to load the ``argument`` successfully short-circuits and
            returns.

        Raises
        ------
        :class:`RuntimeError`
            None of the :attr:`inner_parsers` succeeded to load the ``argument``.

        """
        if not argument and self.optional:
            # Quick-return: if no argument was provided and the parser is
            # optional, just return None without trying any parsers.
            return typing.cast(_T, None)

        # Try all parsers sequentially. If any succeeds, return the result.
        for parser in self.inner_parsers:
            with contextlib.suppress(Exception):
                return await parser.loads(argument)

        msg = "Failed to parse input to any type in the Union."
        raise RuntimeError(msg)

    async def dumps(self, argument: _T, /) -> str:
        """Dump a union of types into a string.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

            This finds a parser that is registered for the type of the provided
            ``argument``.

        Raises
        ------
        :class:`RuntimeError`:
            None of the :attr:`inner_parsers` succeeded to dump the ``argument``.

        """
        if not argument and self.optional:
            return ""

        # TODO: Maybe add contextlib.suppress?
        for parser in self.inner_parsers:
            with contextlib.suppress(Exception):
                return await parser.dumps(argument)

        if self.optional and not self.strict:
            # Act like the NoneParser with strict=False dumped the argument.
            return ""

        msg = f"Failed to parse input {argument!r} to any type in the Union."
        raise RuntimeError(msg)


@parser_base.register_parser_for(typing.Literal)  # pyright: ignore[reportArgumentType]
@attrs.define(slots=True, init=False)
class LiteralParser(parser_base.Parser[_T], typing.Generic[_T]):
    options: typing.Sequence[_T]
    inner_parser: parser_api.Parser[_T]

    def __init__(
        self,
        *options: _T,
        inner_parser: parser_api.Parser[_T],
    ) -> None:
        self.options = options
        self.inner_parser = inner_parser

    @classmethod
    def default(cls, type_: type[_T], /) -> typing_extensions.Self:
        assert typing.get_origin(type_) == typing.Literal
        args: tuple[_T] = typing.get_args(type_)

        args_iter = iter(args)
        arg_type = type(next(args_iter))
        for arg in args_iter:
            if not isinstance(arg, arg_type):
                msg = (
                    "Literal parsers only support literals where all options are of the same type."
                )
                raise TypeError(msg)

        return cls(*args, inner_parser=parser_base.get_parser(arg_type))

    async def loads(self, argument: str, /) -> _T:
        value = await self.inner_parser.loads(argument)

        assert value in self.options

        return value

    async def dumps(self, argument: _T, /) -> str:
        if argument not in self.options:
            msg = (
                f"{argument!r} is not a valid option for this parser."
                f" Expected any of {', '.join(map(repr, self.options))}"
            )
            raise ValueError(msg)

        return await self.inner_parser.dumps(argument)
