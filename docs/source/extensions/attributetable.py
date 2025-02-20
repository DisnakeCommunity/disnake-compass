"""Sphinx attributetable extension."""

# pyright: reportUnknownMemberType = false

from __future__ import annotations

import asyncio
import collections
import importlib
import inspect
import re
import typing

import typing_extensions
from docutils import nodes
from sphinx import addnodes
from sphinx.locale import _
from sphinx.util.docutils import SphinxDirective

if typing.TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment
    from sphinx.writers.html import HTMLTranslator


class SphinxExtensionMeta(typing.TypedDict, total=False):
    version: str
    env_version: int
    parallel_read_safe: bool
    parallel_write_safe: bool


class attributetable(nodes.General, nodes.Element):
    pass


class attributetablecolumn(nodes.General, nodes.Element):
    pass


class attributetabletitle(nodes.Referential, nodes.TextElement):
    pass


class attributetableplaceholder(nodes.General, nodes.Element):
    pass


class attributetablebadge(nodes.TextElement):
    pass


class attributetable_item(nodes.Part, nodes.Element):
    pass


def visit_attributetable_node(self: HTMLTranslator, node: nodes.Element) -> None:
    class_ = typing.cast(str, node["python-class"])
    self.body.append(f'<div class="py-attribute-table" data-move-to-id="{class_}">')


def visit_attributetablecolumn_node(self: HTMLTranslator, node: nodes.Element) -> None:
    self.body.append(self.starttag(node, "div", CLASS="py-attribute-table-column"))


def visit_attributetabletitle_node(self: HTMLTranslator, node: nodes.Element) -> None:
    self.body.append(self.starttag(node, "span"))


def visit_attributetablebadge_node(self: HTMLTranslator, node: nodes.Element) -> None:
    """Add a class to each badge of the type that it is."""
    badge_type = typing.cast(str, node["badge-type"])
    if badge_type not in (
        "coroutine",
        "decorator",
        "method",
        "classmethod",
        "attribute",
    ):
        msg = f"badge_type {badge_type} is currently unsupported"
        raise RuntimeError(msg)
    attributes: typing.Dict[typing.Literal["class"], str] = {
        "class": f"badge-{badge_type}",
    }
    self.body.append(self.starttag(node, "span", **attributes))


def visit_attributetable_item_node(self: HTMLTranslator, node: nodes.Element) -> None:
    self.body.append(self.starttag(node, "li"))


def depart_attributetable_node(self: HTMLTranslator, _node: nodes.Element) -> None:
    self.body.append("</div>")


def depart_attributetablecolumn_node(
    self: HTMLTranslator,
    _node: nodes.Element,
) -> None:
    self.body.append("</div>")


def depart_attributetabletitle_node(self: HTMLTranslator, _node: nodes.Element) -> None:
    self.body.append("</span>")


def depart_attributetablebadge_node(self: HTMLTranslator, _node: nodes.Element) -> None:
    self.body.append("</span>")


def depart_attributetable_item_node(self: HTMLTranslator, _node: nodes.Element) -> None:
    self.body.append("</li>")


_name_parser_regex = re.compile(r"(?P<module>[\w.]+\.)?(?P<name>\w+)")


class PyAttributeTable(SphinxDirective):
    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}  # noqa: RUF012

    def parse_name(self, content: str) -> typing.Tuple[str, typing.Optional[str]]:
        match = _name_parser_regex.match(content)
        path, name = match.groups() if match else (None, None)
        if path:
            modulename = path.rstrip(".")
        else:
            modulename = self.env.temp_data.get("autodoc:module")
            if not modulename:
                modulename = self.env.ref_context.get("py:module")
        if modulename is None:
            msg = f"modulename somehow None for {content} in {self.env.docname}."
            raise RuntimeError(msg)

        return modulename, name

    def run(self) -> typing.List[nodes.Node]:
        content = typing.cast(str, self.arguments[0]).strip()
        node = attributetableplaceholder("")
        modulename, name = self.parse_name(content)
        node["python-doc"] = self.env.docname
        node["python-module"] = modulename
        node["python-class"] = name
        node["python-full-name"] = f"{modulename}.{name}"
        return [node]


def build_lookup_table(env: BuildEnvironment) -> typing.Dict[str, typing.List[str]]:
    # Given an environment, load up a lookup table of
    # full-class-name: objects
    result: typing.DefaultDict[str, typing.List[str]] = collections.defaultdict(list)
    domain = env.domains["py"]

    ignored = {
        "data",
        "exception",
        "module",
        "class",
    }

    for fullname, _unused, objtype, _unused, _unused, _unused in domain.get_objects():
        if objtype in ignored:
            continue

        classname, _unused, child = fullname.rpartition(".")
        result[classname].append(child)

    return result


class TableElement(typing.NamedTuple):
    fullname: str
    label: str
    badge: typing.Optional[attributetablebadge]


def process_attributetable(app: Sphinx, doctree: nodes.document, _docname: str) -> None:
    env = app.builder.env

    lookup = build_lookup_table(env)
    doc_iter = typing.cast(
        typing.Iterator[nodes.document],
        doctree.findall(attributetableplaceholder),
    )
    for node in doc_iter:
        modulename = typing.cast(str, node["python-module"])
        classname = typing.cast(str, node["python-class"])
        fullname = typing.cast(str, node["python-full-name"])
        groups = get_class_results(lookup, modulename, classname, fullname)
        table = attributetable("")
        for label, subitems in groups.items():
            if not subitems:
                continue
            table.append(
                class_results_to_node(
                    _(label),
                    sorted(subitems, key=lambda c: c.label),
                    fullname,
                ),
            )

        table["python-class"] = fullname

        if not table:
            node.replace_self([])
        else:
            node.replace_self([table])


def _is_classvar(ann: typing.Union[str, type]) -> bool:
    if isinstance(ann, str):
        return ann.startswith(("typing.ClassVar", "typing_extensions.ClassVar"))

    return typing.get_origin(ann) in (typing.ClassVar, typing_extensions.ClassVar)


def get_class_results(
    lookup: typing.Dict[str, typing.List[str]],
    modulename: str,
    name: str,
    fullname: str,
) -> typing.Dict[str, typing.List[TableElement]]:
    module = importlib.import_module(modulename)
    cls: type = getattr(module, name)

    groups: typing.Dict[str, typing.List[TableElement]] = {
        "Attributes": [],
        "Methods": [],
    }

    try:
        members = lookup[fullname]
    except KeyError:
        return groups

    anns: typing.Dict[str, typing.Any] = {}

    for attr in members:
        attrlookup = f"{fullname}.{attr}"
        key = "Attributes"
        badge = None
        label = attr
        value = None

        for base in cls.__mro__[:-1]:
            value = base.__dict__.get(attr)
            anns.update(getattr(base, "__annotations__", {}))
            if value is not None:
                break

        if value is not None:
            doc = value.__doc__ or ""
            if asyncio.iscoroutinefunction(value) or doc.startswith("|coro|"):
                key = "Methods"
                badge = attributetablebadge("async", "async")
                badge["badge-type"] = _("coroutine")
            elif isinstance(value, classmethod):
                key = "Methods"
                badge = attributetablebadge("cls", "cls")
                badge["badge-type"] = "classmethod"
            elif inspect.isfunction(value):
                if doc.lstrip().startswith(("A decorator", "A shortcut decorator")):
                    # finicky but surprisingly consistent
                    badge = attributetablebadge("@", "@")
                    badge["badge-type"] = _("decorator")
                    key = "Methods"
                else:
                    key = "Methods"
                    badge = attributetablebadge("def", "def")
                    badge["badge-type"] = _("method")
            elif attr in anns and _is_classvar(anns[attr]):
                key = "Attributes"
                badge = attributetablebadge("classvar", "classvar")
                badge["badge-type"] = _("attribute")
        elif attr in anns and _is_classvar(anns[attr]):
            key = "Attributes"
            badge = attributetablebadge("classvar", "classvar")
            badge["badge-type"] = _("attribute")

        groups[key].append(TableElement(fullname=attrlookup, label=label, badge=badge))

    return groups


def class_results_to_node(
    key: str,
    elements: typing.List[TableElement],
    fullname: str,
) -> attributetablecolumn:
    titleref = nodes.reference(
        "",
        "",
        nodes.Text(key),
        internal=True,
        refuri=f"#{fullname.replace('.', '-')}-{key}".lower(),
        anchorname="",
    )
    title = attributetabletitle("", "", titleref)
    ul = nodes.bullet_list("")
    ul["classes"].append("py-attribute-table-list")
    for element in elements:
        ref = nodes.reference(
            "",
            "",
            nodes.Text(element.label),
            internal=True,
            refuri="#" + element.fullname,
            anchorname="",
        )
        para = addnodes.compact_paragraph("", "", ref)
        if element.badge is not None:
            ul.append(attributetable_item("", element.badge, para))
        else:
            ul.append(attributetable_item("", para))

    return attributetablecolumn("", title, ul)


def setup(app: Sphinx) -> typing.Dict[str, bool]:
    app.add_directive("attributetable", PyAttributeTable)
    app.add_node(
        attributetable,
        html=(visit_attributetable_node, depart_attributetable_node),
    )
    app.add_node(
        attributetablecolumn,
        html=(visit_attributetablecolumn_node, depart_attributetablecolumn_node),
    )
    app.add_node(
        attributetabletitle,
        html=(visit_attributetabletitle_node, depart_attributetabletitle_node),
    )
    app.add_node(
        attributetablebadge,
        html=(visit_attributetablebadge_node, depart_attributetablebadge_node),
    )
    app.add_node(
        attributetable_item,
        html=(visit_attributetable_item_node, depart_attributetable_item_node),
    )
    app.add_node(attributetableplaceholder)
    app.connect("doctree-resolved", process_attributetable)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
