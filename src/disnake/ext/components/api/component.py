"""Protocols for components and component managers."""

from __future__ import annotations

import typing

import disnake
from disnake.ext import commands

if typing.TYPE_CHECKING:
    import typing_extensions

__all__: typing.Sequence[str] = (
    "RichComponent",
    "RichButton",
    "RichSelect",
    "ComponentManager",
)


_T = typing.TypeVar("_T")

AnyBot = typing.Union[commands.Bot, commands.InteractionBot]
AnyEmoji = typing.Union[str, disnake.PartialEmoji, disnake.Emoji]
MaybeCoroutine = typing.Union[_T, typing.Coroutine[None, None, _T]]

ComponentT = typing.TypeVar("ComponentT", bound="RichComponent")
"""A type hint for a (subclass of) a disnake-ext-components component.

In practice, this will be any implementation of the :class:`RichButton`,
or :class:`RichSelect` protocols.
"""


@typing.runtime_checkable
class RichComponent(typing.Protocol):
    """The baseline protocol for any kind of component.

    Any and all components must implement this protocol in order to be properly
    handled by disnake-ext-components.
    """

    __slots__: typing.Sequence[str] = ()

    event: typing.ClassVar[str]
    factory: typing.ClassVar[ComponentFactory[RichComponent]]
    manager: typing.ClassVar[typing.Optional[ComponentManager]]

    async def callback(self, interaction: disnake.Interaction, /) -> None:
        """Run the component callback.

        This should be implemented by the user in each concrete component type.

        Parameters
        ----------
        interaction:
            The interaction that caused this button to fire.

        """
        ...

    async def as_ui_component(self) -> disnake.ui.WrappedComponent:
        """Convert this component into a component that can be sent by disnake.

        Returns
        -------
        :class:`WrappedComponent <disnake.ui.WrappedComponent>`
            A component that can be sent by disnake, maintaining the parameters
            and custom id set on this rich component.

        """
        ...


@typing.runtime_checkable
class RichButton(RichComponent, typing.Protocol):
    """Baseline protocol for Button-like components."""

    __slots__: typing.Sequence[str] = ()

    label: typing.Optional[str]
    """The label of the component.

    Either or both this field or the ``emoji`` field must be set.
    """
    style: disnake.ButtonStyle
    """The style of the component.

    This dictates how the button is displayed on discord.
    """
    emoji: typing.Optional[AnyEmoji]
    """The emoji that is to be displayed on this button.

    Either or both this field or the ``emoji`` field must be set.
    """
    disabled: bool
    """Whether or not this button is disabled.

    A disabled button is greyed out on discord, and cannot be pressed.
    Disabled buttons can therefore not cause any interactions, either.
    """

    async def as_ui_component(self) -> disnake.ui.Button[None]:  # noqa: D102
        # <<Docstring inherited from RichComponent>>
        ...


@typing.runtime_checkable
class RichSelect(RichComponent, typing.Protocol):
    """Baseline protocol for Select-like components."""

    __slots__: typing.Sequence[str] = ()

    placeholder: typing.Optional[str]
    """The placeholder of the component.

    This shows when nothing is selected, or shows nothing if set to
    :data:``None``.
    """
    min_values: int
    """The minimum number of values the user must select.

    This must lie between 1 and 25, inclusive.
    """
    max_values: int
    """The maximum number of values the user may select.

    This must lie between 1 and 25, inclusive.
    """
    disabled: bool
    """Whether or not this button is disabled.

    A disabled select is greyed out on discord, and cannot be used.
    Disabled selects can therefore not cause any interactions, either.
    """

    async def as_ui_component(  # noqa: D102
        self,
    ) -> disnake.ui.BaseSelect[typing.Any, typing.Any, None]:
        # <<Docstring inherited from RichComponent>>
        ...


class ComponentManager(typing.Protocol):
    """The baseline protocol for component managers.

    Component managers keep track of disnake-ext-components' special components
    and ensure they smoothly communicate with disnake's bots. Since this relies
    on listener functionality, component managers are incompatible with
    :class:`disnake.Client`-classes.

    To register a component to a component manager, use :meth:`register`.
    Without registering your components, they will remain unresponsive.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def name(self) -> str:
        """The name of this manager.

        Used in :func:`get_manager`. This functions similar to loggers, where a
        parent-child relationship is denoted with a ".". For example, a manager
        "foo.bar" has parent "foo", which has the root manager as parent.
        """
        ...

    @property
    def children(self) -> typing.Collection[ComponentManager]:
        """The children of this component manager."""
        ...

    @property
    def components(self) -> typing.Mapping[str, typing.Type[RichComponent]]:
        """The components registered to this manager or any of its children.

        In case a custom implementation is made, special care must be taken to
        ensure that these do not desync when a child's components are updated.
        """
        ...

    @property
    def parent(self) -> typing.Optional[ComponentManager]:
        """The parent of this manager.

        Returns :data:`None` in case this is the root manager.
        """
        ...

    def make_identifier(self, component_type: typing.Type[RichComponent]) -> str:
        """Make an identifier for the provided component class.

        This is used to store the component in :attr:`components`, and to
        determine which component's callback should be fired when an interaction
        is received.

        Parameters
        ----------
        component_type
            The type of component for which to make an identifier.

        Returns
        -------
        str
            The component type's identifier.

        """
        ...

    def get_identifier(self, custom_id: str) -> typing.Tuple[str, typing.Sequence[str]]:
        """Extract the identifier and parameters from a custom id.

        This is used to check whether the identifier is registered in
        :attr:`components`.

        Parameters
        ----------
        custom_id
            The custom id from which to extract the identifier.

        """
        ...

    async def make_custom_id(self, component: RichComponent) -> str:
        """Make a custom id from the provided component.

        This can then be used later to reconstruct the component without any
        state or data loss.

        Parameters
        ----------
        component
            The component for which to create a custom id.

        Returns
        -------
        str
            A custom id that fully represents the provided component.

        """
        ...

    async def parse_interaction(
        self, interaction: disnake.Interaction
    ) -> typing.Optional[RichComponent]:
        """Parse an interaction and construct a rich component from it.

        In case the interaction does not match any component registered to this
        manager, this method will simply return :data:`None`.

        Parameters
        ----------
        interaction
            The interaction to parse. This should, under normal circumstances,
            be either a :class:`disnake.MessageInteraction` or
            :class:`disnake.ModalInteraction`.

        Returns
        -------
        :class:`RichComponent`
            The component if the interaction was caused by a component
            registered to this manager.
        :data:`None`
            The interaction was not related to this manager.

        """
        ...

    def register_component(
        self, component_type: typing.Type[ComponentT]
    ) -> typing.Type[ComponentT]:
        r"""Register a component to this component manager.

        This returns the provided class, such that this method can serve as a
        decorator.

        Parameters
        ----------
        component_type
            The component class to register.

        Returns
        -------
        :class:`type`\[:data:`.ComponentT`]
            The component class that was just registered.

        """
        ...

    def deregister_component(self, component_type: typing.Type[RichComponent]) -> None:
        """Deregister a component from this component manager.

        After deregistration, the component will no be tracked, and its
        callbacks can no longer fire until it is re-registered.

        Parameters
        ----------
        component_type
            The component class to deregister.

        Returns
        -------
        type[RichComponent]
            The component class that was just deregistered.

        """

    def add_to_bot(self, bot: AnyBot) -> None:
        """Register this manager to the provided bot.

        This is required to make components registered to this manager
        responsive.

        This method registers the :meth:`invoke` callback as an event to the
        bot for the :obj:`disnake.on_message_interaction` and
        :obj:`disnake.on_modal_submit` events.

        .. note::
            There is no need to separately register every manager you make.
            In general, it is sufficient to only register the root manager as
            the root manager will contain all components of its children.
            That is, the root manager contains *all* registered components, as
            every other manager is a child of the root manager.

        Parameters
        ----------
        bot
            The bot to which to register this manager.

        Raises
        ------
        RuntimeError
            This manager has already been registered to the provided bot.

        """
        ...

    def remove_from_bot(self, bot: AnyBot) -> None:
        """Deregister this manager from the provided bot.

        This makes all components registered to this manager unresponsive.

        Parameters
        ----------
        bot
            The bot from which to deregister this manager.

        Raises
        ------
        RuntimeError
            This manager is not registered to the provided bot.

        """
        ...

    async def invoke(self, interaction: disnake.Interaction) -> None:
        """Try to invoke a component with the given interaction.

        If this manager has no registered component that matches the interaction,
        it is silently ignored. Otherwise, the interaction will be parsed into
        a fully fledged component, and its callback will then be invoked.

        Parameters
        ----------
        interaction
            The interaction with which to try to invoke a component callback.

        """
        ...


class ComponentFactory(typing.Protocol[ComponentT]):
    """The baseline protocol for any kind of component factory.

    Any and all component factories must implement this protocol in order to be
    properly handled by disnake-ext-components.

    A component factory handles creating a component instance from a custom id
    by running all individual fields' parsers and aggregating the result into
    a component instance.
    """

    __slots__: typing.Sequence[str] = ()

    @classmethod
    def from_component(
        cls,
        component: typing.Type[RichComponent],
        /,
    ) -> typing_extensions.Self:
        """Create a component factory from the provided component.

        This takes the component's fields into account and generates the
        corresponding parser types for each field if a parser was not provided
        manually for that particular field.

        Parameters
        ----------
        component
            The component for which to create a component factory.

        """
        ...

    # TODO: Update docstring
    async def load_params(
        self,
        source: typing.Any,  # noqa: ANN401
        params: typing.Sequence[str],
        /,
    ) -> typing.Mapping[str, object]:
        """Create a new component instance from the provided custom id.

        This requires the custom id to already have been decomposed into
        individual fields. This is generally done using the
        :meth:`ComponentManager.get_identifier` method.

        Parameters
        ----------
        source
            The source object to use for creating the component instance.
        params
            A mapping of field name to to-be-parsed field values.

        """
        # TODO: Return an ext-components specific conversion error.
        ...

    async def dump_params(self, component: ComponentT, /) -> typing.Mapping[str, str]:
        """Dump a component into a new custom id string.

        This converts the component's individual fields back into strings and
        and uses these strings to build a new custom id. This is generally done
        using the :meth:`ComponentManager.get_identifier` method.

        Parameters
        ----------
        component
            The component to dump into a custom id.

        """
        ...

    async def build_component(
        self,
        source: typing.Any,  # noqa: ANN401
        params: typing.Sequence[str],
        component_params: typing.Optional[typing.Mapping[str, object]],
    ) -> ComponentT:
        """Create a new component instance from the provided interaction.

        This requires the custom id to already have been decomposed into
        individual fields. This is generally done by the component manager.

        Parameters
        ----------
        source
            The source object to use for creating the component instance.
        params
            A sequence of to-be-parsed field values.
        component_params
            A mapping of parameters that is to be directly passed to the
            component constructor.

        """
        ...
