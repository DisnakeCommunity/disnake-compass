"""Lightweight contextvar-based dependency injection-adjacent solution."""

from __future__ import annotations

import contextvars
import typing

import typing_extensions

from disnake_compass.internal import omit

__all__: typing.Sequence[str] = (
    "register_dependencies",
    "reset_dependencies",
    "resolve_dependency",
)

_T = typing.TypeVar("_T")
TokenMap: typing_extensions.TypeAlias = typing.Mapping[
    type[typing.Any],
    contextvars.Token[object],
]

# XXX:  This actually introduces a memory leak when combined with hot-reloading
#       as old types will never be cleared from the dependency map. Since hot-
#       reloading in production environments is ill-advised anyway, I don't
#       think it's worth adding a lot more complexity to circumvent it.
#       ...Unless, of course, someone can come up with a better approach.
DEPENDENCY_MAP: dict[type[typing.Any], contextvars.ContextVar[typing.Any]] = {}


def _get_contextvar_for(dependency_type: type[_T], /) -> contextvars.ContextVar[_T]:
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


def register_dependencies(*dependencies: object) -> TokenMap:
    r"""Register any number of dependencies.

    This returns a mapping of :class:`contextvars.Token`\s that should be
    passed to :func:`reset_dependencies` for cleanup.

    While dependencies are registered, :func:`resolve_dependency` can be used
    to get it for the current async context.

    Parameters
    ----------
    *dependencies:
        Objects to register as dependencies. Their type must be hashable.
        (This should automatically hold for most classes.)

    Returns
    -------
    typing.Dict[typing.Type[typing.Any], contextvars.Token[object]]
        A mapping of the types of the registered dependencies to contextvar
        tokens used to reset their respective contextvars. This is meant to be
        passed to :func:`reset_dependencies` for cleanup.

    """
    tokens: dict[type, contextvars.Token[object]] = {}
    for dependency in dependencies:
        dependency_type = type(dependency)
        tokens[dependency_type] = _get_contextvar_for(dependency_type).set(dependency)

    return tokens


def reset_dependencies(tokens: TokenMap) -> None:
    """Reset dependencies that are no longer in use.

    This is meant to be used in conjunction with :func:`register_dependencies`.

    Parameters
    ----------
    tokens:
        A mapping of the types of the registered dependencies to contextvar
        tokens used to reset their respective contextvars. This mapping is
        created and returned by :func:`register_dependencies`.

    """
    for dependency_type, token in tokens.items():
        _get_contextvar_for(dependency_type).reset(token)


def resolve_dependency(
    dependency_type: type[_T],
    default: omit.Omissible[_T] = omit.Omitted,
) -> _T:
    """Resolve a dependency given a type and an optional default.

    If a dependency was set using :func:`register_dependency` in the current
    context, this function returns it. If it is not found, the default is
    returned instead. If no default was provided, a :class:`LookupError` is
    raised instead.

    Parameters
    ----------
    dependency_type:
        The type to resolve to an object.
    default:
        The default to use if resolving did not return an object.

    Returns
    -------
    object
        The resolved dependency or the default.

    Raises
    ------
    :class:`LookupError`
        The dependency type could not be resolved and no default was provided.

    """
    context = _get_contextvar_for(dependency_type)
    resolved = context.get(omit.Omitted)
    if not omit.is_omitted(resolved):
        return resolved

    if not omit.is_omitted(default):
        return default

    msg = f"Failed to resolve dependency for type {dependency_type.__name__}."
    raise LookupError(msg)
