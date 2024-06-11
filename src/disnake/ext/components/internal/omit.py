"""Sentinels for omissible parameters."""

import enum
import typing

import typing_extensions

__all__: typing.Sequence[str] = ("Omitted", "Omissible", "OmittedNoneOr", "is_omitted")


class OmittedType(enum.Enum):
    """Sentinel type for omissible parameters."""

    Omitted = enum.auto()


Omitted = OmittedType.Omitted
"""Sentinel value for omissible parameters."""

_T = typing.TypeVar("_T")
Omissible = typing.Union[OmittedType, _T]
OmittedNoneOr = typing.Optional[Omissible[_T]]


def is_omitted(obj: Omissible[_T]) -> typing_extensions.TypeIs[OmittedType]:
    """Check whether a value was omitted."""
    return obj is Omitted
