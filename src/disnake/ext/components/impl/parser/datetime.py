"""Parser implementations for types provided in the datetime package."""

import datetime
import enum
import typing

from disnake.ext.components.impl.parser import base as parser_base
from disnake.ext.components.impl.parser import builtins as builtins_parsers

__all__: typing.Sequence[str] = (
    "DateParser",
    "DatetimeParser",
    "TimeParser",
    "TimedeltaParser",
    "TimezoneParser",
)

_VALID_BASE_10 = frozenset([10**i for i in range(-6, 0)])


class Resolution(float, enum.Enum):
    r"""The resolution with which :class:`datetime.datetime`\s etc. are stored."""

    MICROS = 1e-6
    """Microsecond resolution.

    This is the default for the datetime module, but often more than required.
    """
    MILLIS = 1e-3
    """Millisecond resolution.

    Rounds the datetime **down** to the nearest microsecond.
    """
    SECONDS = 1
    """Second resolution.

    Rounds the datetime **down** to the nearest second.
    """
    MINUTES = 60 * SECONDS
    """Minute resolution.

    Rounds the datetime **down** to the nearest minute.
    """
    HOURS = 60 * MINUTES
    """Hour resolution.

    Rounds the datetime **down** to the nearest hour.
    """
    DAYS = 24 * HOURS
    """Day resolution.

    Rounds the datetime **down** to the nearest day.
    """


# TODO: Is forcing the use of timezones on users really a parser_based move?
#       Probably.
@parser_base.register_parser_for(datetime.datetime)
class DatetimeParser(parser_base.Parser[datetime.datetime]):
    r"""Parser type with support for datetimes.

    Parameters
    ----------
    resolution:
        The resolution with which to store :class:`~datetime.datetime`\s in custom ids.
        Defaults to :obj:`Resolution.SECONDS`.
    timezone:
        The timezone to use for parsing.
        Defaults to :obj:`datetime.timezone.utc`.
    strict:
        Whether this parser is in strict mode.
        Defaults to ``True``.
    int_parser:
        The :class:`IntParser` to use internally for this parser.

    """

    resolution: typing.Union[int, float]
    r"""The resolution with which to store :class:`~datetime.datetime`\s in seconds.

    .. warning::
        The resolution must be greater than ``1e-6``, and if the resolution is
        smaller than 1, it **must** be a power of 10. If the resolution is
        greater than 1, it is coerced into an integer.

    .. note::
        Python datetime objects have microsecond accuracy. For most
        applications, this is much more precise than necessary.
        Since custom id space is limited, seconds was chosen as the default.
    """

    timezone: datetime.timezone
    """The timezone to use for parsing.
    Datetimes returned by :meth:`loads` will always be of this timezone.

    This is *not* stored in the custom id.
    """

    strict: bool
    """Whether the parser is in strict mode.

    If the parser is in strict mode, :meth:`loads` requires the provided
    datetime object to be of the correct :attr:`timezone`.
    """

    int_parser: builtins_parsers.IntParser
    """The :class:`IntParser` to use internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default datetime parser will also return compressed results.
    """

    def __init__(
        self,
        *,
        resolution: typing.Union[int, float] = Resolution.SECONDS,
        timezone: datetime.timezone = datetime.timezone.utc,
        strict: bool = True,
        int_parser: typing.Optional[builtins_parsers.IntParser] = None,
    ) -> None:
        if resolution < 1e-6:
            msg = f"Resolution must be greater than 1e-6, got {resolution}."
            raise ValueError(msg)

        if resolution < 1 and resolution not in _VALID_BASE_10:
            # TODO: Verify whether this doesn't false-negative
            msg = f"Resolutions smaller than 1 must be a power of 10, got {resolution}."
            raise ValueError(msg)

        self.resolution = resolution
        self.timezone = timezone
        self.strict = strict
        self.int_parser = int_parser or builtins_parsers.IntParser.default(int)

    async def loads(self, argument: str, /) -> datetime.datetime:
        """Load a datetime from a string.

        This uses the underlying :attr:`int_parser`.

        The returned datetime is always of the specified :attr:`timezone`.

        Parameters
        ----------
        argument:
            The string that is to be converted into a datetime.

        """
        return datetime.datetime.fromtimestamp(
            await self.int_parser.loads(argument) * self.resolution,
            tz=self.timezone,
        )

    async def dumps(self, argument: datetime.datetime, /) -> str:
        """Dump a datetime into a string.

        This uses the underlying :attr:`int_parser`.

        If :attr:`strict` is set to ``True``, this will fail if the provided
        ``argument`` does not have a timezone set. Otherwise, a timezone-naive
        datetime will automatically get its timezone set to :attr:`timezone`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        Raises
        ------
        :class:`ValueError`:
            Either the parser is set to strict and the provided datetime was
            timezone-naive, or the provided datetime's timezone does not match
            that of the parser.

        """
        if self.strict:
            if not argument.tzinfo:
                msg = "Strict DatetimeParsers can only load timezone-aware datetimes."
                raise ValueError(msg)
        else:
            argument = argument.replace(tzinfo=self.timezone)

        if argument.tzinfo != self.timezone:
            msg = (
                "Cannot dump the provided datetime object due to a mismatch in"
                f" timezones. (expected: {self.timezone}, got: {argument.tzinfo})"
            )
            raise ValueError(msg)

        timestamp = argument.timestamp()
        if self.resolution != 0:
            timestamp //= self.resolution

        return await self.int_parser.dumps(int(timestamp))


@parser_base.register_parser_for(datetime.timedelta)
class TimedeltaParser(parser_base.Parser[datetime.timedelta]):
    r"""Parser type with support for :class:`datetime.timedelta`\s.

    Parameters
    ----------
    resolution:
        The resolution with which to store :class:`~datetime.timedelta`\s in custom ids.
        Defaults to :obj:`Resolution.SECONDS`.
    timezone:
        The timezone to use for parsing.
        Defaults to :obj:`datetime.timezone.utc`.
    strict:
        Whether this parser is in strict mode.
        Defaults to ``True``.
    int_parser:
        The :class:`IntParser` to use internally for this parser.

    """

    resolution: typing.Union[int, float]
    r"""The resolution with which to store :class:`~datetime.timedelta`\s in seconds.

    .. warning::
        The resolution must be greater than ``1e-6``, and if the resolution is
        smaller than 1, it **must** be a power of 10. If the resolution is
        greater than 1, it is coerced into an integer.

    .. note::
        Python datetime objects have microsecond accuracy. For most
        applications, this is much more precise than necessary.
        Since custom id space is limited, seconds was chosen as the default.
    """

    int_parser: builtins_parsers.IntParser
    """The :class:`IntParser` to use internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default datetime parser will also return compressed results.
    """

    def __init__(
        self,
        *,
        resolution: typing.Union[int, float] = Resolution.SECONDS,
        int_parser: typing.Optional[builtins_parsers.IntParser] = None,
    ) -> None:
        if resolution < 1e-6:
            msg = f"Resolution must be greater than 1e-6, got {resolution}."
            raise ValueError(msg)

        if resolution < 1 and resolution not in _VALID_BASE_10:
            # TODO: Verify whether this doesn't false-negative
            msg = f"Resolutions smaller than 1 must be a power of 10, got {resolution}."
            raise ValueError(msg)

        self.resolution = resolution
        self.int_parser = int_parser or builtins_parsers.IntParser.default(int)

    async def loads(self, argument: str, /) -> datetime.timedelta:
        """Load a timedelta from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The string that is to be converted into a timedelta.

        """
        seconds = await self.int_parser.loads(argument) * self.resolution
        return datetime.timedelta(seconds=seconds)

    async def dumps(self, argument: datetime.timedelta, /) -> str:
        """Dump a timedelta into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return await self.int_parser.dumps(int(argument.total_seconds() // self.resolution))


@parser_base.register_parser_for(datetime.date)
class DateParser(parser_base.Parser[datetime.date]):
    """Parser type with support for dates.

    Parameters
    ----------
    int_parser:
        The :class:`IntParser` to use internally for this parser.

    """

    int_parser: builtins_parsers.IntParser
    """The :class:`IntParser` to use internally for this parser.

    Since the default integer parser uses base-36 to "compress" numbers, the
    default date parser will also return compressed results.
    """

    def __init__(self, *, int_parser: typing.Optional[builtins_parsers.IntParser]) -> None:
        self.int_parser = int_parser or builtins_parsers.IntParser.default(int)

    async def loads(self, argument: str, /) -> datetime.date:
        """Load a date from a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The string that is to be converted into a date.

        """
        return datetime.date.fromordinal(await self.int_parser.loads(argument))

    async def dumps(self, argument: datetime.date, /) -> str:
        """Dump a datetime into a string.

        This uses the underlying :attr:`int_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return await self.int_parser.dumps(datetime.date.toordinal(argument))


@parser_base.register_parser_for(datetime.time)
class TimeParser(parser_base.Parser[datetime.time]):
    r"""Parser type with support for times.

    .. important::
        Unlike :class:`DatetimeParser` etc., resolution for this class is set
        via the underlying :attr:`timedelta_parser`. Note that this class *does*
        proxy it through the :attr:`precision` property, which supports both
        getting and setting.

    Parameters
    ----------
    timezone:
        The timezone to use for parsing.
        Defaults to :obj:`datetime.timezone.utc`.
    strict:
        Whether this parser is in strict mode.
        Defaults to ``True``.
    timedelta_parser:
        The :class:`TimedeltaParser` to use internally for this parser.

    """

    timezone: datetime.timezone
    """The timezone to use for parsing.
    Times returned by :meth:`loads` will always be of this timezone.

    This is *not* stored in the custom id.
    """

    strict: bool
    """Whether the parser is in strict mode.

    If the parser is in strict mode, :meth:`loads` requires the provided
    datetime object to be of the correct :attr:`timezone`.
    """

    timedelta_parser: TimedeltaParser
    """The :class:`TimedeltaParser` to use internally for this parser.

    Since the default timedelta parser uses base-36 to "compress" numbers, the
    default datetime parser will also return compressed results.
    """

    def __init__(
        self,
        *,
        timezone: datetime.timezone = datetime.timezone.utc,
        timedelta_parser: typing.Optional[TimedeltaParser] = None,
        strict: bool = True,
    ) -> None:
        self.timezone = timezone
        self.timedelta_parser = (
            timedelta_parser or TimedeltaParser.default(datetime.timedelta)
        )
        self.strict = strict

    @property
    def resolution(self) -> typing.Union[int, float]:
        r"""The resolution with which to store :class:`~datetime.time`\s in seconds.

        .. warning::
            The resolution must be greater than ``1e-6``, and if the resolution is
            smaller than 1, it **must** be a power of 10. If the resolution is
            greater than 1, it is coerced into an integer.

        .. note::
            Python time objects have microsecond accuracy. For most
            applications, this is much more precise than necessary.
            Since custom id space is limited, seconds was chosen as the default.
        """
        return self.timedelta_parser.resolution

    @resolution.setter
    def resolution(self, resolution: typing.Union[int, float]) -> None:
        self.timedelta_parser.resolution = resolution

    async def loads(self, argument: str, /) -> datetime.time:
        """Load a time from a string.

        This uses the underlying :attr:`timedelta_parser`.

        The returned time is always of the specified :attr:`timezone`.

        Parameters
        ----------
        argument:
            The string that is to be converted into a time.

        """
        dt = datetime.datetime.min + await self.timedelta_parser.loads(argument)
        return dt.time().replace(tzinfo=self.timezone)

    async def dumps(self, argument: datetime.time, /) -> str:
        """Dump a time into a string.

        This uses the underlying :attr:`timedelta_parser`.

        If :attr:`strict` is set to ``True``, this will fail if the provided
        ``argument`` does not have a timezone set. Otherwise, a timezone-naive
        time will automatically get its timezone set to :attr:`timezone`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        Raises
        ------
        :class:`ValueError`:
            Either the parser is set to strict and the provided time was
            timezone-naive, or the provided time's timezone does not match
            that of the parser.

        """
        if self.strict:
            if not argument.tzinfo:
                msg = "Strict TimeParsers can only load timezone-aware times."
                raise ValueError(msg)
        else:
            argument = argument.replace(tzinfo=self.timezone)

        if argument.tzinfo != self.timezone:
            msg = (
                "Cannot dump the provided time object due to a mismatch in"
                f" timezones. (expected: {self.timezone}, got: {argument.tzinfo})"
            )
            raise ValueError(msg)

        return await self.timedelta_parser.dumps(
            datetime.timedelta(
                hours=argument.hour,
                minutes=argument.minute,
                seconds=argument.second,
                microseconds=argument.microsecond,
            )
        )


@parser_base.register_parser_for(datetime.timezone)
class TimezoneParser(parser_base.Parser[datetime.timezone]):
    r"""Parser type with support for :class:`~datetime.timezone`\s.

    .. important::
        Unlike :class:`DatetimeParser` etc., resolution for this class is set
        via the underlying :attr:`timedelta_parser`. Note that this class *does*
        proxy it through the :attr:`precision` property, which supports both
        getting and setting.

    Parameters
    ----------
    timedelta_parser:
        The :class:`TimedeltaParser` to use internally for this parser.

    """

    timedelta_parser: TimedeltaParser
    """The :class:`TimedeltaParser` to use internally for this parser.

    Since the default timedelta parser uses base-36 to "compress" numbers, the
    default datetime parser will also return compressed results.
    """

    def __init__(self, *, timedelta_parser: typing.Optional[TimedeltaParser] = None) -> None:
        self.timedelta_parser = timedelta_parser or TimedeltaParser()

    @property
    def resolution(self) -> typing.Union[int, float]:
        r"""The resolution with which to store :class:`~datetime.time`\s in seconds.

        .. warning::
            The resolution must be greater than ``1e-6``, and if the resolution is
            smaller than 1, it **must** be a power of 10. If the resolution is
            greater than 1, it is coerced into an integer.

        .. note::
            Python time objects have microsecond accuracy. For most
            applications, this is much more precise than necessary.
            Since custom id space is limited, seconds was chosen as the default.
        """
        return self.timedelta_parser.resolution

    @resolution.setter
    def resolution(self, resolution: typing.Union[int, float]) -> None:
        self.timedelta_parser.resolution = resolution

    async def loads(self, argument: str, /) -> datetime.timezone:
        """Load a timezone from a string.

        This uses the underlying :attr:`timedelta_parser`.

        Parameters
        ----------
        argument:
            The string that is to be converted into a timezone.

        """
        return datetime.timezone(await self.timedelta_parser.loads(argument))

    async def dumps(self, argument: datetime.timezone, /) -> str:
        """Dump a timezone into a string.

        This uses the underlying :attr:`timedelta_parser`.

        Parameters
        ----------
        argument:
            The value that is to be dumped.

        """
        return await self.timedelta_parser.dumps(argument.utcoffset(None))
