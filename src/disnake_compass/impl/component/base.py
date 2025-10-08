"""Implementation of component base classes.

To easily integrate with disnake-compass, it is recommended to inherit
from any of these base classes. In any case, it is very much recommended to at
least use the `ComponentMeta` metaclass. Without this, a lot of internal
functionality will have to be manually re-implemented.
"""

from __future__ import annotations

import abc
import sys
import typing

import attrs
import typing_extensions

from disnake_compass import fields as fields
from disnake_compass.api import component as component_api
from disnake_compass.api import parser as parser_api
from disnake_compass.impl import factory as factory_impl
from disnake_compass.impl import parser as parser_impl

if typing.TYPE_CHECKING:
    import disnake

__all__: typing.Sequence[str] = ("ComponentBase",)


_T = typing.TypeVar("_T")

MaybeCoroutine: typing.TypeAlias = _T | typing.Coroutine[None, None, _T]
_AnyAttr: typing_extensions.TypeAlias = "attrs.Attribute[typing.Any]"


def _is_attrs_pass(namespace: dict[str, typing.Any]) -> bool:
    """Check if attrs has already influenced the class' namespace.

    Note that we check the namespace instead of using `attrs.has`, because
    `attrs.has` would always return `True` for a class inheriting an attrs class,
    and we specifically need to distinguish between the two passes inside
    `ComponentMeta.__new__`.
    """
    return namespace.get("__attrs_attrs__") is not None


def _determine_parser(
    attribute: _AnyAttr,
    overwrite: _AnyAttr | None,
    *,
    required: bool = True,
) -> parser_api.Parser[typing.Any] | None:
    parser = fields.get_parser(attribute)
    if parser:
        return parser

    if overwrite:
        parser = fields.get_parser(overwrite)
        if parser:
            return parser

    if required:
        return parser_impl.get_parser(attribute.type or str)

    return None


def _eval_type(cls: type, annotation: typing.Any) -> typing.Any:  # noqa: ANN401
    # Get the module globals in which the class was defined. This is the most
    # probable candidate in which to find the type annotations' definitions.
    #
    # For the most part, this should be safe. Conflicts where e.g. a component
    # inheriting from RichButton but not defining _AnyEmoji in their own module
    # are safe, because the type has already been passed through this function
    # when the RichButton class was initially created.
    cls_globals = sys.modules[cls.__module__].__dict__

    if isinstance(annotation, str):
        annotation = typing.ForwardRef(annotation, is_argument=False)

    # Evaluate the typehint with the provided globals.
    return typing._eval_type(annotation, cls_globals, None)  # pyright: ignore  # noqa: PGH003, SLF001


def _assert_valid_overwrite(attribute: _AnyAttr, overwrite: _AnyAttr) -> None:
    if fields.FieldMetadata.FIELDTYPE not in overwrite.metadata:
        return

    # The field was defined using fields.field / fields.internal / etc.
    # Ensure the overwrite matches the original field type.

    attribute_type = fields.get_field_type(overwrite)
    overwrite_type = fields.get_field_type(attribute)

    if overwrite_type is not attribute_type:
        new = (attribute_type.name or "<unknown>").lower()
        old = (overwrite_type.name or "<unknown>").lower()
        msg = (
            f"Invalid field override. Field {overwrite.name} is defined as"
            f" a(n) {new} field, but was overwritten as a(n) {old} field."
        )
        raise TypeError(msg)


def _is_custom_id_field(field: _AnyAttr) -> bool:
    return fields.get_field_type(field, fields.FieldType.CUSTOM_ID) is fields.FieldType.CUSTOM_ID


def _field_transformer(
    cls: type,
    attributes: list[_AnyAttr],
) -> list[_AnyAttr]:
    super_attributes: dict[str, _AnyAttr] = (
        {field.name: field for field in fields.get_fields(cls)} if attrs.has(cls) else {}
    )

    finalised_attributes: list[_AnyAttr] = []
    for attribute in attributes:
        super_attribute = super_attributes.get(attribute.name)

        # Ensure all forward-references are evaluated.
        evolved = attribute.evolve(type=_eval_type(cls, attribute.type))

        if super_attribute:
            # This field overwrites a pre-existing field. Merge metadata and
            # ensure the parser isn't overwritten if the new value is None.
            _assert_valid_overwrite(super_attribute, attribute)
            metadata = {**super_attribute.metadata, **evolved.metadata}

        else:
            # Not an overwrite, ensure the fieldtype is set to CUSTOM_ID if not
            # already provided.
            metadata = {
                fields.FieldMetadata.FIELDTYPE: fields.FieldType.CUSTOM_ID,
                **evolved.metadata,
            }

        # TODO: Make copy of parser instead of using the same instance
        metadata[fields.FieldMetadata.PARSER] = _determine_parser(
            evolved,
            super_attribute,
            # Fields only need a parser if
            # - The component is concrete,
            # - The field is a custom-id field.
            # In case of an overwrite, we check the field type of the super-field.
            required=(
                not typing_extensions.is_protocol(cls)
                and _is_custom_id_field(super_attribute or attribute)
            ),
        )

        # Apply finalised metadata.
        finalised_attributes.append(evolved.evolve(metadata=metadata))

    return finalised_attributes


@typing_extensions.dataclass_transform(
    kw_only_default=True,
    field_specifiers=(fields.field, fields.internal, fields.meta),
)
class ComponentMeta(type(typing.Protocol)):
    """Metaclass for all disnake-compass component types.

    It is **highly** recommended to use this metaclass for any class that
    should interface with the components api exposed by
    `disnake-compass`.

    This metaclass handles :mod:`attrs` class generation, custom id completion,
    interfacing with component managers, parser and factory generation, and
    automatic slotting.
    """

    def __new__(  # noqa: PYI034
        metacls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, typing.Any],
    ) -> ComponentMeta:
        # NOTE: This is run twice for each new class; once for the actual class
        #       definition, and once more by attrs.define(). We ensure we only
        #       run the full class creation logic once.

        cls = super().__new__(metacls, name, bases, namespace)

        # If this is attrs' pass, return immediately.
        if _is_attrs_pass(namespace):
            return cls

        cls = attrs.define(cls, slots=True, kw_only=True, field_transformer=_field_transformer)

        # NOTE: Pyright complains about RichComponent being a data protocol
        #       here, but this is a false-positive, as the only non-method
        #       member is __slots__.
        assert issubclass(cls, component_api.RichComponent)  # pyright: ignore[reportGeneralTypeIssues]
        factory_cls = (
            factory_impl.NoopFactory
            if typing_extensions.is_protocol(cls)
            else factory_impl.ComponentFactory[typing.Any]
        )

        cls.set_factory(factory_cls.from_component(cls))
        return typing.cast(ComponentMeta, cls)


@typing.runtime_checkable
class ComponentBase(component_api.RichComponent, typing.Protocol, metaclass=ComponentMeta):
    """Overarching base class for any kind of component."""

    _factory: typing.ClassVar[component_api.ComponentFactory[typing_extensions.Self]]
    _manager: typing.ClassVar[component_api.ComponentManager | None] = None

    @classmethod
    def get_manager(cls) -> component_api.ComponentManager:  # noqa: D102
        # <<Docstring inherited from component_api.RichComponent>>

        if cls._manager is None:
            msg = f"Component {cls.__qualname__} is not yet registered to a manager."
            raise RuntimeError(msg)

        return cls._manager

    @classmethod
    def set_manager(cls, manager: component_api.ComponentManager | None) -> None:  # noqa: D102
        # <<Docstring inherited from component_api.RichComponent>>

        cls._manager = manager

    @classmethod
    def get_factory(cls) -> component_api.ComponentFactory[typing_extensions.Self]:
        r"""Get the factory that built this component instance.

        .. note::
            Component base classes can be declared as a subclass of
            :class:`~typing.Protocol`\s, which tells disnake_compass that this
            component is a 'template' and should not be instantiable.
            In this case, this attribute defaults to a :class:`~NoopFactory`.

            In case a concrete component subclass is created, a matching
            :class:`~ComponentFactory` is automatically generated instead.
        """
        return cls._factory

    @classmethod
    def set_factory(cls, factory: component_api.ComponentFactory[typing_extensions.Self]) -> None:  # noqa: D102
        # <<Docstring inherited from component_api.RichComponent>>

        cls._factory = factory

    async def as_ui_component(  # noqa: D102
        self,
        manager: component_api.ComponentManager,
        /,
    ) -> disnake.ui.WrappedComponent:
        # <<Docstring inherited from component_api.RichComponent>>
        ...

    async def make_custom_id(self, manager: component_api.ComponentManager | None, /) -> str:
        """Make a custom id from this component given its current state.

        The generated custom id will contain the full state of the component,
        such that it be used to entirely reconstruct the component later.

        Because parameter to string conversion supports asynchronous callbacks,
        this has to be an async function instead of e.g. a property.

        .. note::
            As the logic for translating a component to and from a custom id
            resides inside the component manager, the component *must* be
            registered to a manager to use this method.

        Parameters
        ----------
        manager:
            The manager to use to make a custom id for this component. This is
            only relevant if you have multiple managers for the same component.
            Defaults to the root manager.

        Returns
        -------
        str:
            The custom id representing the full state of this component.

        """
        if manager is None:
            manager = self.get_manager()

        return await manager.make_custom_id(self)

    @abc.abstractmethod
    async def callback(  # pyright: ignore[reportIncompatibleMethodOverride]  # noqa: D102
        self,
        inter: disnake.MessageInteraction[disnake.Client],
        /,
    ) -> None:
        # <<docstring inherited from component_api.RichButton>>

        # NOTE: We narrow the interaction type down to a disnake.MessageInteraction
        #       here. This isn't typesafe, but it's just cleaner for the user.
        ...
