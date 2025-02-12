"""Lightweight contextvar-based dependency injection-adjacent solution."""

from __future__ import annotations

import contextvars
import typing

from disnake.ext.components.internal import omit

__all__: typing.Sequence[str] = (
    "register_dependencies",
    "reset_dependencies",
    "resolve_dependency",
)

_T = typing.TypeVar("_T")

# XXX:  This actually introduces a memory leak when combined with hot-reloading
#       as old types will never be cleared from the dependency map. Since hot-
#       reloading in production environments is ill-advised anyway, I don't
#       think it's worth adding a lot more complexity to circumvent it.
#       ...Unless, of course, someone can come up with a better approach.
DEPENDENCY_MAP: typing.Dict[typing.Type[typing.Any], contextvars.ContextVar[typing.Any]] = {}


def _get_contextvar_for(dependency_type: typing.Type[_T], /) -> contextvars.ContextVar[_T]:
    if dependency_type in DEPENDENCY_MAP:
        return DEPENDENCY_MAP[dependency_type]

    # Resolve subclass of registered type and save it to speed up future lookups.
    for registered_type, context in DEPENDENCY_MAP.items():
        if issubclass(registered_type, dependency_type):
            DEPENDENCY_MAP[dependency_type] = context
            return context

    # Insert missing dependency type, use a name that is unlikely to lead to conflicts.
    name = f"__disnake_ext_components__{dependency_type.__name__}__"
    context = DEPENDENCY_MAP[dependency_type] = contextvars.ContextVar[_T](name)
    return context


def register_dependencies(*dependencies: object) -> typing.Dict[typing.Type[typing.Any], contextvars.Token[object]]:
    tokens: typing.Dict[type, contextvars.Token[object]] = {}
    for dependency in dependencies:
        dependency_type = type(dependency)
        tokens[dependency_type] = _get_contextvar_for(dependency_type).set(dependency)

    return tokens


def reset_dependencies(tokens: typing.Dict[typing.Type[typing.Any], contextvars.Token[object]]) -> None:
    for dependency_type, token in tokens.items():
        _get_contextvar_for(dependency_type).reset(token)


def resolve_dependency(
    dependency_type: typing.Type[_T],
    default: omit.Omissible[_T] = omit.Omitted,
) -> _T:
    context = _get_contextvar_for(dependency_type)
    resolved = context.get(omit.Omitted)
    if not omit.is_omitted(resolved):
        return resolved

    elif not omit.is_omitted(default):
        return default

    msg = f"Failed to resolve dependency for type {dependency_type.__name__}."
    raise LookupError(msg)
