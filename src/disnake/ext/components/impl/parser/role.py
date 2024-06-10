"""Parser implementations for disnake role types."""

from __future__ import annotations

import typing

import disnake
from disnake.ext.components.impl.parser import base, snowflake

__all__: typing.Sequence[str] = (
    "GetRoleParser",
    "RoleParser",
)


class GetRoleParser(  # noqa: D101
    base.Parser[disnake.Role],
    is_default_for=(disnake.Role,),
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    def loads(  # noqa: D102
        self, inter: disnake.Interaction, argument: str
    ) -> disnake.Role:
        # <<docstring inherited from parser_api.Parser>>

        if inter.guild is None:
            msg = (
                "Impossible to get a role from an"
                " interaction that doesn't come from a guild."
            )
            raise TypeError(msg)
        role = inter.guild.get_role(int(argument))

        if role is None:
            msg = f"Could not find a role with id {argument!r}."
            raise LookupError(msg)

        return role


class RoleParser(  # noqa: D101
    base.Parser[disnake.Role],
    is_default_for=(disnake.Role,),
):
    # <<docstring inherited from parser_api.Parser>>

    def __init__(self) -> None:
        super().__init__()
        self.dumps = snowflake.snowflake_dumps

    async def loads(  # noqa: D102
        self, inter: disnake.Interaction, argument: str
    ) -> disnake.Role:
        # <<docstring inherited from parser_api.Parser>>

        if inter.guild is None:
            msg = (
                "Impossible to fetch a role from an"
                " interaction that doesn't come from a guild."
            )
            raise TypeError(msg)
        role = (
            inter.guild.get_role(int(argument))
            or disnake.utils.get(await inter.guild.fetch_roles(), id=int(argument))
        )  # fmt: skip

        # a role id coming from a custom_id could be of a deleted role object
        # so we're handling that possibility
        if role is None:
            msg = f"Could not find a role with id {argument!r}."
            raise LookupError(msg)

        return role
