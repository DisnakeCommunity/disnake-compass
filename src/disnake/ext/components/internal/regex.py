"""Regex utility functions."""

import re
import typing

__all__: typing.Sequence[str] = ("escape", "format_to_pattern")


# NOTE: copy-paste from re.escape; minus {}
_ESCAPE_TRANS = {i: "\\" + chr(i) for i in b"()[]?*+-|^$\\.&~# \t\n\r\v\f"}


def escape(pattern: str) -> str:
    """Similar to re.escape, except this ignores {} format specifiers."""
    return pattern.translate(_ESCAPE_TRANS)


def format_to_pattern(
    format_str: str,
    /,
    *,
    flags: typing.Optional[int] = None,
) -> typing.Pattern[str]:
    """Create a regex pattern from a format string with named fields.

    Parameters
    ----------
    format_str:
        The format string to turn into a :class:`re.Pattern`.
    flags:
        The flags to use for the compiled regex pattern. This defaults to the
        same flags as :func:`re.compile`.

    Returns
    -------
    :class:`re.Pattern`[:class:`str`]:
        A compiled regex pattern that can match any string created by
        formatting the provided format string.

    """
    pattern = re.sub(
        # Match {} format groups, strip e.g. :0f and !r specifiers.
        r"\{(\w+)(?:\:.*?|\!.*?)?\}",
        # Replace with regex named group, keeping the format group's name.
        r"(?P<\1>.*?)",
        # Escape any regex special chars except format groups.
        escape(format_str),
    )

    return re.compile(pattern, flags=re.UNICODE if flags is None else flags)
