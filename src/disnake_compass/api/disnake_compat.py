"""Re-exports of some disnake internal types related to components.

These types are mostly meant for internal use to appropriately typehint methods
that take disnake components, and is therefore not exposed.

These types are documented for clarity in documentation lookups.
"""

import typing

import disnake

# NOTE: Keep up to date with disnake types...

ActionRowMessageComponent = disnake.ui.Button[typing.Any] | disnake.ui.Select[typing.Any]
"""All valid disnake UI components for action rows.

Note that, when using 'components-V1', all components must be sent via action
rows.

In particular, see:

- :class:`disnake.ui.Button`,
- :class:`disnake.ui.BaseSelect`.
"""

MessageTopLevelComponentV2 = (
    disnake.ui.Section
    | disnake.ui.TextDisplay
    | disnake.ui.MediaGallery
    | disnake.ui.File
    | disnake.ui.Separator
    | disnake.ui.Container
)
"""All valid top-level disnake UI components for a components-V2 message.

In particular, see:

- :class:`disnake.ui.Section`,
- :class:`disnake.ui.TextDisplay`,
- :class:`disnake.ui.MediaGallery`,
- :class:`disnake.ui.File`,
- :class:`disnake.ui.Separator`,
- :class:`disnake.ui.Container`.
"""

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
"""Valid input to the `components` keyword in disnake send/edit methods.

This expects one of:

- A single top-level component,
    - If this is a :obj:`MessageTopLevelComponentV2` V2 is automatically assumed,
    - otherwise, sending defaults to V1.
- A sequence of components,
    - If this is a sequence of action rows V1 is automatically assumed,
    - If this is a sequence of :obj:`MessageTopLevelComponentV2` V2 is
      automatically assumed,
    - otherwise, V1 is assumed and components are automatically distributed
      across action rows.
- A sequence of sequences of components.
    - The inner sequences are automatically interpreted as action rows and
      V1 is assumed.
"""

MessageComponents = ComponentInput[ActionRowMessageComponent, MessageTopLevelComponentV2]
