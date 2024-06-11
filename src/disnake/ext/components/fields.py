"""Field implementations extending :func:`attrs.field`."""

from __future__ import annotations

import enum
import functools
import typing

import attrs
import typing_extensions

if typing.TYPE_CHECKING:
    from disnake.ext.components.api import parser as parser_api

__all__: typing.Sequence[str] = ("field",)


_T = typing_extensions.TypeVar("_T", default=typing.Any)


class FieldMetadata(enum.Enum):
    """Enum containing keys for field metadata."""

    PARSER = enum.auto()
    """Metadata key to store parser information."""
    FIELDTYPE = enum.auto()
    """Metadata key to store field type information. See :class:`FieldType`."""


class FieldType(enum.Flag):
    """Flag containing field metadata values for the field type.

    Note that a field can only ever be one of these types. This is a flag for
    the sole reason of facilitating unions in lookups using :func:`get_fields`.
    """

    INTERNAL = enum.auto()
    """Internal field that does not show up in the component's init signature."""
    CUSTOM_ID = enum.auto()
    """Field parsed into/from the component's custom id."""
    SELECT = enum.auto()
    """Field parsed from a select component's selected values."""
    MODAL = enum.auto()
    """Field parsed from a modal component's modal values."""

    @classmethod
    def ALL(cls) -> FieldType:
        """Meta-value for all field types.

        Mainly intended for use in :func:`get_fields`.
        """
        return _ALL_FIELD_TYPES


_ALL_FIELD_TYPES = functools.reduce(FieldType.__or__, FieldType)
_ALL_FIELD_TYPES._name_ = "ALL()"  # This makes it render nicer in docs.


def get_parser(
    field: attrs.Attribute[typing.Any],
) -> typing.Optional[parser_api.Parser]:
    """Get the user-provided parser of the provided field.

    Parameters
    ----------
    field:
        The field for which to get the :class:`components.api.Parser`.

    Returns
    -------
    :class:`components.api.Parser`
        The user-provided parser of the provided field.
    :data:`None`
        The field's parser was automatically inferred.

    """
    return field.metadata.get(FieldMetadata.PARSER)


def get_field_type(
    field: attrs.Attribute[typing.Any], default: typing.Optional[FieldType] = None
) -> FieldType:
    """Get the :class:`FieldType` of the field.

    Parameters
    ----------
    field:
        The field of which to get the field type.
    default:
        The default value to use if the field doesn't have a :class:`FieldType`
        set.

    Returns
    -------
    :class:`FieldType`
        The type of the provided field.

    Raises
    ------
    :class:`TypeError`
        The provided field does not have a field type set, and no default was
        provided. The most common cause of this is using
        :func:`attrs.field` instead of :func:`components.field() <.field>` to
        define a field.

    """
    if FieldMetadata.FIELDTYPE not in field.metadata:
        if default:
            return default

        msg = (
            f"Field {field.name!r} does not contain the proper metadata to be"
            f" recognised by disnake-ext-components. Please only construct fields"
            f" through functions provided by disnake-ext-components."
            f" See the 'disnake.ext.components.fields' submodule for possibilities."
        )
        raise TypeError(msg)

    return field.metadata[FieldMetadata.FIELDTYPE]


def is_field_of_type(field: attrs.Attribute[typing.Any], kind: FieldType) -> bool:
    """Check whether or not a field is marked as the provided :class:`FieldType`.

    Parameters
    ----------
    field:
        The field to check.
    kind:
        The :class:`FieldType` to check for.

    Returns
    -------
    :class:`bool`
        Whether the provided field was of the provided :class:`FieldType`.

    """
    set_type = field.metadata.get(FieldMetadata.FIELDTYPE)
    return bool(set_type and set_type & kind)  # Check if not None, then check if match.


def get_fields(
    cls: type,
    /,
    *,
    kind: FieldType = _ALL_FIELD_TYPES,
) -> typing.Sequence[attrs.Attribute[typing.Any]]:
    r"""Get the attributes of an attrs class.

    This wraps :func:`attrs.fields` to be less strict typing-wise and has
    special handling for internal fields.

    Parameters
    ----------
    cls:
        The class of which to get the fields.
    kind:
        The kind(s) of fields to return. Can be any combination of
        :class:`FieldType`\s.

    """
    return [field for field in attrs.fields(cls) if is_field_of_type(field, kind)]


def field(
    default: typing.Union[_T, typing.Literal[attrs.NOTHING]] = attrs.NOTHING,
    *,
    parser: typing.Optional[parser_api.Parser[_T]] = None,
) -> _T:
    r"""Define a custom ID field for the component.

    The type annotation for this field is used to parse incoming custom ids.

    This is a wrapper around :func:`attrs.field`.

    .. note::
        In most cases, simply using a typehint will suffice to define a field.
        This function is generally only needed if you wish to supply a default
        value or custom parser.

    .. note::
        Fields created this way always have ``kw_only=True`` set.

    Parameters
    ----------
    default:
        The default value for this field. The type of the default should match
        that of the type annotation.
    parser:
        The parser to use for converting this field to and from a string.
        The type of the parser should match that of the type annotation.

    Returns
    -------
    :func:`Field <attrs.field>`\[``T``]
        A new field with the provided default and/or parser.

    """
    return attrs.field(
        default=typing.cast(_T, default),
        kw_only=True,
        metadata={
            FieldMetadata.FIELDTYPE: FieldType.CUSTOM_ID,
            FieldMetadata.PARSER: parser,
        },
    )


def internal(
    default: _T,
    *,
    frozen: bool = False,
) -> _T:
    r"""Declare a field as internal.

    This is used internally to differentiate component parameters from
    user-defined custom id parameters.

    This is a wrapper around :func:`attrs.field`.

    .. note::
        Fields created this way always have ``kw_only=True`` set.

    Parameters
    ----------
    default:
        The default value for this field. The type of the default should match
        that of the type annotation.
    frozen:
        Whether or not the field should be marked frozen. A frozen field cannot
        be modified after the class has been created.

    Returns
    -------
    :func:`Field <attrs.field>`\[``T``]
        A new field with the provided default and frozen status.

    """
    return attrs.field(
        default=default,
        on_setattr=attrs.setters.frozen if frozen else None,
        metadata={FieldMetadata.FIELDTYPE: FieldType.INTERNAL},
    )
