"""This module does three "important" things

- Provide custom documenters for enums and flags,
- Change class documenter's ordering to prioritise attributes,
- Add 'section labels' within classes.
"""

import enum
import typing

import sphinx
import sphinx.application
import sphinx.config
import sphinx.domains.python
import sphinx_autodoc_typehints
from sphinx.ext import autodoc
from sphinx.locale import _


class ClassDocumenterWithExtraSteps(autodoc.ClassDocumenter):
    priority = autodoc.ClassDocumenter.priority + 1

    order_display_map: typing.ClassVar[typing.Dict[int, str]] = {
        50: _("Methods"),
        60: _("Attributes"),
    }

    def document_members(self, all_members: bool = False) -> None:  # noqa: FBT001, FBT002
        if self.doc_as_attr:
            return

        if (
            self.options.member_order
            or self.config.autodoc_member_order
        ) != "groupwise":  # fmt: skip
            super().document_members(all_members)
            return

        # set current namespace for finding members
        self.env.temp_data["autodoc:module"] = self.modname
        if self.objpath:
            self.env.temp_data["autodoc:class"] = self.objpath[0]

        want_all = (
            all_members or self.options.inherited_members or self.options.members is autodoc.ALL
        )
        # find out which members are documentable
        members_check_module, members = self.get_object_members(want_all)

        # document non-skipped members
        memberdocumenters: list[tuple[autodoc.Documenter, bool]] = []
        for mname, member, isattr in self.filter_members(members, want_all):
            classes = [
                cls
                for cls in self.documenters.values()
                if cls.can_document_member(member, mname, isattr, self)
            ]
            if not classes:
                # don't know how to document this member
                continue
            # prefer the documenter with the highest priority
            # give explicitly separated module name, so that members
            # of inner classes can be documented
            full_mname = f"{self.modname}::" + ".".join((*self.objpath, mname))
            documenter_cls = max(classes, key=lambda cls: cls.priority)
            documenter = documenter_cls(self.directive, full_mname, self.indent)
            memberdocumenters.append((documenter, isattr))

        # NOTE: Personal preference; I'd rather have attributes first.
        memberdocumenters.sort(key=lambda e: (-e[0].member_order, e[0].name))
        source_name = self.get_sourcename()
        last_member_group = 0

        for documenter, isattr in memberdocumenters:
            if documenter.member_order != last_member_group:
                last_member_group = documenter.member_order
                category = self.order_display_map.get(last_member_group)
                if not category:
                    autodoc.logger.warning(
                        "Found member order without display name %i: %s",
                        last_member_group,
                        documenter.objtype,
                    )
                    category = documenter.objtype

                # TODO: Maybe figure out how to actually render this as some
                #       small title thing.
                underline = "^" * len(category)
                self.add_line(f".. _{self.name}-{category}:", source_name)
                self.add_line("", source_name)
                self.add_line(category, source_name)
                self.add_line(underline, source_name)
                self.add_line("", source_name)

            documenter.generate(
                all_members=True,
                real_modname=self.real_modname,
                check_module=members_check_module and not isattr,
            )

        # reset current objects
        self.env.temp_data["autodoc:module"] = None
        self.env.temp_data["autodoc:class"] = None


class EnumDocumenter(ClassDocumenterWithExtraSteps):
    objtype = "enum"
    directivetype = "enum"
    priority = 20
    class_xref = ":class:`~enum.Enum`"

    order_display_map: typing.ClassVar[typing.Dict[int, str]] = {
        50: "METHODS",
        60: "MEMBERS",
    }

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        if not self.options.member_order:
            self.options.member_order = "bysource"  # type: ignore

    @classmethod
    def can_document_member(
        cls,
        member: object,
        membername: str,  # noqa: ARG003
        isattr: bool,  # noqa: ARG003, FBT001
        parent: object,  # noqa: ARG003
    ) -> bool:
        return isinstance(member, enum.EnumMeta) and not issubclass(member, enum.Flag)

    def add_content(self, more_content: typing.Optional[autodoc.StringList]) -> None:
        super().add_content(more_content)

        source_name = self.get_sourcename()
        base = self.object.__bases__[0]
        if not issubclass(base, enum.Enum):
            ann = sphinx_autodoc_typehints.format_annotation(base, self.config)
            self.add_line(f"Member type: {ann}", source_name)
            self.add_line("", source_name)


class FlagDocumenter(EnumDocumenter):
    objtype = "flag"
    directivetype = "flag"
    priority = 25
    class_xref = ":class:`~enum.Flag`"

    @classmethod
    def can_document_member(
        cls,
        member: object,
        membername: str,  # noqa: ARG003
        isattr: bool,  # noqa: ARG003, FBT001
        parent: object,  # noqa: ARG003
    ) -> bool:
        return isinstance(member, enum.EnumMeta) and issubclass(member, enum.Flag)


def setup(app: sphinx.application.Sphinx) -> typing.Dict[str, bool]:
    app.setup_extension("sphinx.ext.autodoc")
    app.add_autodocumenter(ClassDocumenterWithExtraSteps, override=True)
    app.add_autodocumenter(EnumDocumenter)
    app.add_autodocumenter(FlagDocumenter)

    type_registry = app.registry.domains["py"].object_types
    type_registry["enum"] = sphinx.domains.ObjType(_("enum"), "enum", "class", "obj")
    type_registry["flag"] = sphinx.domains.ObjType(_("flag"), "flag", "class", "obj")

    app.add_directive_to_domain("py", "enum", sphinx.domains.python.PyClasslike)
    app.add_directive_to_domain("py", "flag", sphinx.domains.python.PyClasslike)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
