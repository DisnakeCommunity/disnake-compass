"""Standard implementation of the overarching component factory type."""

from __future__ import annotations

import types
import typing

import attrs

from disnake_compass import fields
from disnake_compass.api import component as component_api
from disnake_compass.api import parser as parser_api
from disnake_compass.impl.parser import base as parser_base

if typing.TYPE_CHECKING:
    import typing_extensions

__all__: typing.Sequence[str] = ("ComponentFactory",)


ParserMapping = typing.Mapping[str, parser_api.Parser[typing.Any]]


@attrs.define(slots=True)
class ComponentFactory(
    component_api.ComponentFactory[component_api.ComponentT],
    typing.Generic[component_api.ComponentT],
):
    """Implementation of the overarching component factory type.

    A component factory holds information about all the custom id fields of a
    component, and contains that component's parsers. In most situations, a
    component factory can simply be created using :meth:`from_component`.
    """

    parsers: ParserMapping = attrs.field(converter=types.MappingProxyType)  # pyright: ignore[reportGeneralTypeIssues]
    """A mapping of custom id field name to that field's parser."""
    component: type[component_api.ComponentT]
    """The component type that this factory builds."""

    @classmethod
    def from_component(  # noqa: D102
        cls,
        component: type[component_api.RichComponent],
    ) -> typing_extensions.Self:
        # <<docstring inherited from api.components.ComponentFactory>>
        parser: parser_api.Parser[typing.Any] | None

        parsers: dict[str, parser_api.Parser[typing.Any]] = {}
        for field in fields.get_fields(component, kind=fields.FieldType.CUSTOM_ID):
            parser = fields.get_parser(field)

            if not parser:
                parser_type = field.type or str
                parser = parser_base.get_parser(parser_type).default(parser_type)

            parsers[field.name] = parser

        return cls(
            parsers,
            typing.cast(type[component_api.ComponentT], component),
        )

    async def load_params(  # noqa: D102
        self,
        params: typing.Sequence[str],
    ) -> typing.Mapping[str, object]:
        # <<docstring inherited from api.components.ComponentFactory>>
        return {
            param: await self.parsers[param].loads(value)
            for param, value in zip(self.parsers, params, strict=True)
            if value  # TODO: Check this, I think this is wrong.
        }

    async def dump_params(  # noqa: D102
        self,
        component: component_api.ComponentT,
    ) -> typing.Mapping[str, str]:
        # <<docstring inherited from api.components.ComponentFactory>>

        return {
            field: await self.parsers[field].dumps(getattr(component, field))
            for field in self.parsers
        }

    async def build_component(  # noqa: D102
        self,
        params: typing.Sequence[str],
        component_params: typing.Mapping[str, object] | None = None,
    ) -> component_api.ComponentT:
        # <<docstring inherited from api.components.ComponentFactory>>

        parsed = await self.load_params(params)
        return self.component(**parsed, **(component_params or {}))


class NoopFactory(component_api.ComponentFactory[typing.Any]):
    """Factory class to make component protocols typesafe.

    Since component protocols cannot be instantiated, building a factory with
    parsers for them does not make sense. Instead, they will receive one of
    these to remain typesafe. Any operation on a NoopFactory will raise
    :class:`NotImplementedError`.
    """

    __slots__: typing.Sequence[str] = ()
    __instance: typing.ClassVar[typing_extensions.Self | None] = None

    def __new__(cls) -> typing_extensions.Self:
        if cls.__instance is not None:
            return cls.__instance  # pyright: ignore[reportReturnType]

        cls.__instance = self = super().__new__(cls)
        return self

    @classmethod
    def from_component(
        cls,
        _: type[component_api.RichComponent],
    ) -> typing_extensions.Self:
        # <<docstring inherited from api.components.ComponentFactory>>

        return cls()

    async def load_params(self, *_: object) -> typing.NoReturn:
        # <<docstring inherited from api.components.ComponentFactory>>

        raise NotImplementedError

    async def dump_params(self, *_: object) -> typing.NoReturn:
        # <<docstring inherited from api.components.ComponentFactory>>

        raise NotImplementedError

    async def build_component(
        self,
        params: typing.Sequence[str],
        component_params: typing.Mapping[str, object] | None = None,
    ) -> typing.NoReturn:
        # <<docstring inherited from api.components.ComponentFactory>>

        raise NotImplementedError

    def __repr__(self) -> str:
        return "<NoopFactory>"
