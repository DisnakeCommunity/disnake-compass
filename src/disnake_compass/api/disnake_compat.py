"""Re-exports of some disnake internal types related to components."""

import typing

import disnake

# NOTE: Keep up to date with disnake types...

ActionRowMessageComponent = disnake.ui.Button[typing.Any] | disnake.ui.Select[typing.Any]
MessageTopLevelComponentV2 = (
    disnake.ui.Section
    | disnake.ui.TextDisplay
    | disnake.ui.MediaGallery
    | disnake.ui.File
    | disnake.ui.Separator
    | disnake.ui.Container
)
ModalTopLevelComponent_ = disnake.ui.TextDisplay | disnake.ui.Label
ActionRowChildT = typing.TypeVar("ActionRowChildT", bound=disnake.ui.WrappedComponent)
NonActionRowChildT = typing.TypeVar(
    "NonActionRowChildT",
    bound=MessageTopLevelComponentV2 | ModalTopLevelComponent_,
)
AnyUIComponentInput = ActionRowChildT | disnake.ui.ActionRow[ActionRowChildT] | NonActionRowChildT
ComponentInput = (
    AnyUIComponentInput[ActionRowChildT, NonActionRowChildT]
    | typing.Sequence[
        AnyUIComponentInput[ActionRowChildT, NonActionRowChildT] | typing.Sequence[ActionRowChildT]
    ]
)
MessageComponents = ComponentInput[ActionRowMessageComponent, MessageTopLevelComponentV2]
