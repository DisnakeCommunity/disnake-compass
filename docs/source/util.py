"""Small utilities for Sphinx documentation."""

import importlib.util
import inspect
import os
import sys
import typing

import sphinx.config
import sphinx_autodoc_typehints as original
from sphinx.util import inspect as sphinx_inspect

__all__ = (
    "apply_autodoc_typehints_patch",
    "format_annotation",
    "get_module_path",
    "make_linkcode_resolver",
)


NoneType = type(None)


def get_module_path() -> str:
    """Get the filepath for the module."""
    _spec = importlib.util.find_spec("disnake_compass")
    if not (_spec and _spec.origin):
        raise RuntimeError  # this should never happen

    return os.path.dirname(_spec.origin)


def make_linkcode_resolver(
    module_path: str, repo_url: str, git_ref: str,
) -> typing.Callable[[str, typing.Mapping[str, typing.Any]], typing.Optional[str]]:
    """Return a linkcode resolver for the provided module path and repo data."""

    def linkcode_resolve(
        domain: str, info: typing.Mapping[str, typing.Any],
    ) -> typing.Optional[str]:
        if domain != "py":
            return None

        try:
            obj: typing.Any = sys.modules[info["module"]]
            for part in info["fullname"].split("."):
                obj = getattr(obj, part)
            obj = inspect.unwrap(obj)

            if isinstance(obj, property):
                obj = inspect.unwrap(obj.fget)  # pyright: ignore

            path: typing.Any = inspect.getsourcefile(obj)
            path = os.path.relpath(path, start=module_path)
            src, lineno = inspect.getsourcelines(obj)

        except Exception:  # noqa: BLE001
            return None

        path = f"{path}#L{lineno}-L{lineno + len(src) - 1}"
        return f"{repo_url}/blob/{git_ref}/src/disnake/ext/components/{path}"

    return linkcode_resolve


def format_annotation(  # noqa: PLR0911, PLR0912, PLR0915
    annotation: typing.Any, config: sphinx.config.Config,  # noqa: ANN401
) -> str:
    """Format the annotation."""
    if typehints_formatter := getattr(config, "typehints_formatter", None):
        formatted = typehints_formatter(annotation, config)
        if formatted is not None:
            return formatted

    # Special cases
    if isinstance(annotation, typing.ForwardRef):
        return annotation.__forward_arg__
    if annotation in (None, NoneType):
        return ":py:obj:`None`"
    if annotation is Ellipsis:
        return ":py:data:`...<Ellipsis>`"

    if isinstance(annotation, tuple):
        return original.format_internal_tuple(annotation, config)  # pyright: ignore

    if isinstance(annotation, sphinx_inspect.TypeAliasForwardRef):
        return str(annotation)

    try:
        module = original.get_annotation_module(annotation)
        class_name = original.get_annotation_class_name(annotation, module)
        args = original.get_annotation_args(annotation, module, class_name)
    except ValueError:
        return str(annotation).strip("'")

    # Redirect all typing_extensions types to the stdlib typing module
    if module == "typing_extensions":
        module = "typing"

    elif module == "_io":
        module = "io"

    full_name = f"{module}.{class_name}" if module != "builtins" else class_name
    fully_qualified: bool = getattr(config, "typehints_fully_qualified", False)
    prefix = "" if fully_qualified or full_name == class_name else "~"
    role = (
        "data"
        if module == "typing"
        and class_name in original._PYDATA_ANNOTATIONS  # pyright: ignore
        else "class"
    )
    args_format = "\\[{}]"
    formatted_args: str = ""

    always_use_bars_union: bool = getattr(config, "always_use_bars_union", True)
    is_bars_union = full_name == "types.UnionType" or (
        always_use_bars_union and type(annotation).__qualname__ == "_UnionGenericAlias"
    )
    if is_bars_union:
        full_name = ""

    # Some types require special handling
    if full_name == "typing.NewType":
        args_format = f"\\(``{annotation.__name__}``, {{}})"
        role = "class" if sys.version_info >= (3, 10) else "func"

    # NOTE: Modified to return :py:data:`NameOfTypeVar`
    elif full_name in {"typing.TypeVar", "typing.ParamSpec"}:
        role = "data"
        full_name = annotation.__name__

    elif full_name == "typing.Optional":
        args = tuple(x for x in args if x is not NoneType)

    elif full_name in ("typing.Union", "types.UnionType") and NoneType in args:
        if len(args) == 2:
            full_name = "typing.Optional"
            role = "data"
            args = tuple(x for x in args if x is not type(None))
        else:
            simplify_optional_unions: bool = getattr(
                config, "simplify_optional_unions", True,
            )
            if not simplify_optional_unions:
                full_name = "typing.Optional"
                role = "data"
                args_format = f"\\[:py:data:`{prefix}typing.Union`\\[{{}}]]"
                args = tuple(x for x in args if x is not type(None))

    elif (
        full_name in ("typing.Callable", "collections.abc.Callable")
        and args
        and args[0] is not ...
    ):
        fmt = [format_annotation(arg, config) for arg in args]
        formatted_args = f"\\[\\[{', '.join(fmt[:-1])}], {fmt[-1]}]"

    elif full_name == "typing.Literal":
        formatted_args = f"\\[{', '.join(f'``{arg!r}``' for arg in args)}]"

    elif is_bars_union:
        return " | ".join([format_annotation(arg, config) for arg in args])

    # TODO: Maybe figure out some way of having Self actually link to the class.
    #       Low priority though.

    if args and not formatted_args:
        try:
            iter(args)
        except TypeError:
            fmt = [format_annotation(args, config)]
        else:
            fmt = [format_annotation(arg, config) for arg in args]
        formatted_args = args_format.format(", ".join(fmt))

    escape = "\\ " if formatted_args else ""
    return f":py:{role}:`{prefix}{full_name}`{escape}{formatted_args}"


def apply_autodoc_typehints_patch() -> None:
    """Apply the sphinx-ext-autodoc monkeypatch."""
    original.format_annotation = format_annotation
