"""Sentinels for omissible parameters."""

import enum
import typing

import typing_extensions

__all__: typing.Sequence[str] = ("Omissible", "Omitted", "OmittedNoneOr", "is_omitted")


class OmittedType(enum.Enum):
    """Sentinel type for omissible parameters."""

    Omitted = enum.auto()

    def __bool__(self) -> typing.Literal[False]:
        return False


Omitted: typing.Final[typing.Literal[OmittedType.Omitted]] = OmittedType.Omitted
"""Sentinel value for omissible parameters."""

_T = typing.TypeVar("_T")
Omissible: typing.TypeAlias = OmittedType | _T
OmittedNoneOr: typing.TypeAlias = Omissible[_T] | None


def is_omitted(obj: Omissible[_T]) -> typing_extensions.TypeIs[OmittedType]:
    """Check whether a value was omitted."""
    return obj is Omitted
