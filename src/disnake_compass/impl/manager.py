"""Default implementation of the component manager api."""

from __future__ import annotations

import contextlib
import contextvars
import logging
import sys
import typing
import weakref

import attrs
import disnake
import typing_extensions

from disnake_compass import fields
from disnake_compass.api import component as component_api
from disnake_compass.internal import di, omit

__all__: typing.Sequence[str] = ("ComponentManager", "check_manager", "get_manager")


_LOGGER = logging.getLogger(__name__)
_ROOT = sys.intern("root")
_COMPONENT_EVENT = sys.intern("on_message_interaction")
_MODAL_EVENT = sys.intern("on_modal_submit")

_COMPONENT_CTX: contextvars.ContextVar[tuple[component_api.RichComponent, str]] = (
    contextvars.ContextVar("_COMPONENT_CTX")
)


T = typing.TypeVar("T")


class DependencyProviderFunc(typing.Protocol):
    def __call__(
        self,
        manager: ComponentManager,
        *dependencies: object,
    ) -> typing.AsyncGenerator[None, None]: ...


class DependencyProvider(typing.Protocol):
    def __call__(
        self,
        manager: ComponentManager,
        *dependencies: object,
    ) -> typing.AsyncContextManager[None]: ...


DependencyProviderFuncT = typing.TypeVar("DependencyProviderFuncT", bound=DependencyProviderFunc)


CallbackWrapperFunc: typing.TypeAlias = typing.Callable[
    ["ComponentManager", component_api.RichComponent, disnake.Interaction[disnake.Client]],
    typing.AsyncGenerator[None, None],
]
CallbackWrapper: typing.TypeAlias = typing.Callable[
    ["ComponentManager", component_api.RichComponent, disnake.Interaction[disnake.Client]],
    typing.AsyncContextManager[None],
]
CallbackWrapperFuncT = typing.TypeVar("CallbackWrapperFuncT", bound=CallbackWrapperFunc)


ExceptionHandlerFunc: typing.TypeAlias = typing.Callable[
    [
        "ComponentManager",
        component_api.RichComponent,
        disnake.Interaction[disnake.Client],
        Exception,
    ],
    typing.Coroutine[typing.Any, typing.Any, bool | None],
]
ExceptionHandlerFuncT = typing.TypeVar(
    "ExceptionHandlerFuncT",
    bound=ExceptionHandlerFunc,
)

RichComponentT = typing.TypeVar("RichComponentT", bound=component_api.RichComponent)
RichComponentType: typing.TypeAlias = type[component_api.RichComponent]

MessageComponents: typing.TypeAlias = (
    component_api.RichButton
    | disnake.ui.Button[typing.Any]
    | component_api.RichSelect
    | disnake.ui.StringSelect[typing.Any]
    | disnake.ui.ChannelSelect[typing.Any]
    | disnake.ui.RoleSelect[typing.Any]
    | disnake.ui.UserSelect[typing.Any]
    | disnake.ui.MentionableSelect[typing.Any]
)


def _to_ui_component(
    component: disnake.Button | disnake.BaseSelectMenu,
) -> disnake.ui.MessageUIComponent:
    if isinstance(component, disnake.Button):
        return disnake.ui.Button[None].from_component(component)
    if isinstance(component, disnake.StringSelectMenu):
        return disnake.ui.StringSelect[None].from_component(component)
    if isinstance(component, disnake.UserSelectMenu):
        return disnake.ui.UserSelect[None].from_component(component)
    if isinstance(component, disnake.RoleSelectMenu):
        return disnake.ui.RoleSelect[None].from_component(component)
    if isinstance(component, disnake.MentionableSelectMenu):
        return disnake.ui.MentionableSelect[None].from_component(component)
    if isinstance(component, disnake.ChannelSelectMenu):
        return disnake.ui.ChannelSelect[None].from_component(component)

    msg = f"Expected a message component type, got {type(component).__name__!r}."
    raise TypeError(msg)


_MAX_COUNT = 1 << 8 - 1  # 1 byte, starting at 0


def _minimise_count(count: int) -> str:
    # We only need to support counts up to 25, as that is the
    # maximum number of components that can go on a message.
    # Byte-length 1 should support a range of 0~255 inclusive.
    byte = count.to_bytes(1, "little")
    # Decode into a charset that supports these bytes as a single char.
    return byte.decode("latin-1")


_COUNT_CHARS: typing.Final[tuple[str, ...]] = tuple(
    map(_minimise_count, range(25)),
)
_DEFAULT_SEP: typing.Final[str] = sys.intern("|")
_DEFAULT_COUNT: typing.Final = True


@contextlib.asynccontextmanager
async def default_dependency_provider(
    manager: component_api.ComponentManager,  # noqa: ARG001
    *dependencies: object,
) -> typing.AsyncGenerator[None, None]:
    tokens = di.register_dependencies(
        *(dependency for dependency in dependencies if dependency is not None),
    )

    yield

    di.reset_dependencies(tokens)


@contextlib.asynccontextmanager
async def default_callback_wrapper(
    manager: component_api.ComponentManager,  # noqa: ARG001
    component: component_api.RichComponent,  # noqa: ARG001
    interaction: disnake.Interaction[disnake.Client],  # noqa: ARG001
) -> typing.AsyncGenerator[None, None]:
    """Wrap a callback for a component manager.

    This is the default implementation, and is effectively a no-op.
    """
    yield


async def default_exception_handler(
    manager: component_api.ComponentManager,
    component: component_api.RichComponent,
    interaction: disnake.Interaction[disnake.Client],  # noqa: ARG001
    exception: Exception,
) -> bool:
    """Handle an exception that occurs during execution of a component callback.

    This is the default implementation, and simply passes the exception down.
    If it is passed down to the root logger, and the root logger also has this
    default implementation, the exception is logged.
    """
    if manager.name is not _ROOT:
        # Not the root manager, try passing down.
        return False

    # We're at the root logger, and the exception remains unhandled. Log it.

    exc_info = (
        type(exception),
        exception,
        exception.__traceback__.tb_next if exception.__traceback__ else None,
    )

    _LOGGER.exception(
        "An exception was caught on manager %r while handling the callback of"
        " component %r, registered to manager %r:",
        manager.name,
        component,
        component.manager.name if component.manager else "<unknown>",
        exc_info=exc_info,
    )

    return True


@attrs.define
class _ModuleData:
    name: str
    id: int

    @classmethod
    def from_object(cls, obj: object) -> typing_extensions.Self:
        module = sys.modules[obj.__module__]
        return cls(obj.__module__, id(module))

    def is_active(self) -> bool:
        if self.name not in sys.modules:
            return False

        return self.id == id(sys.modules[self.name])

    def is_reload_of(self, other: typing_extensions.Self) -> bool:
        return self.name == other.name and self.id != other.id


class ComponentManager(component_api.ComponentManager):
    """The standard implementation of a component manager.

    Component managers keep track of disnake-compass' special components
    and ensure they smoothly communicate with disnake's clients.

    To register a component to a component manager, use :meth:`register`.
    Without registering your components, they will remain unresponsive.

    To get an instance of a component manager, use :func:`get_manager`. This
    will automatically create missing managers if needed, much like
    :func:`logging.getLogger`. Similarly, managers feature a parent-child
    hierarchy in the same way loggers do. For example, a manager named
    "foo.bar" would be a child of the manager named "foo".

    The topmost manager will always be the root manager, which can be acquired
    through calling :func:`get_manager` without passing a name.

    When a component is invoked on - for example - a manager "foo.bar", it will
    wrap the callback in the :meth:`as_callback_wrapper` wrappers bubbling up.
    That is, the callback is wrapped by the root manager, then "foo",
    then "foo.bar", and finally invoke the callback.

    If any exceptions occur during the wrapping or invocation of the callback,
    the managers' exception handlers will be invoked starting from "foo.bar",
    then "foo", and finally the root manager. If any exception handler returns
    ``True``, the exception is considered handled and any remaining exception
    handlers are skipped.

    Parameters
    ----------
    name:
        The name of the component manager. This should be unique for all live
        component managers.
    count:
        Whether the component manager should insert *one* count character to
        resolve duplicates. Normally, sending two components with the same
        custom id would error. Enabling this ensures custom ids are unique
        by appending an incrementing character. This costs 1 character,
        effectively reducing the maximum custom id length to 99 characters.

        If not set, the manager will use its parents' settings. The default
        set on the root manager is ``True``.
    sep:
        The character(s) to use as separator between custom id parts.

        If not set, the manager will use its parents' settings. The default
        set on the root manager is ``"|"``.
    client:
        The client to which to register this manager. This can be specified at any
        point through :meth:`.add_to_client`.

    """

    __slots__: typing.Sequence[str] = (
        "_children",
        "_client",
        "_components",
        "_count",
        "_counter",
        "_identifiers",
        "_module_data",
        "_name",
        "_sep",
        "handle_exception",
        "set_invocation_dependencies",
        "wrap_callback",
    )

    _client: disnake.Client | None
    _children: set[ComponentManager]
    _components: weakref.WeakValueDictionary[str, RichComponentType]
    _count: bool | None
    _counter: int
    _identifiers: dict[str, str]
    _module_data: dict[str, _ModuleData]
    _name: str
    _sep: str | None

    def __init__(
        self,
        name: str,
        *,
        count: bool | None = None,
        sep: str | None = None,
        client: disnake.Client | None = None,
    ) -> None:
        self._name = name
        self._children = set()
        self._components = weakref.WeakValueDictionary()
        self._identifiers = {}
        self._count = count
        self._counter = 0
        self._module_data = {}
        self._sep = sep
        self.set_invocation_dependencies: DependencyProvider = default_dependency_provider
        self.wrap_callback: CallbackWrapper = default_callback_wrapper
        self.handle_exception: ExceptionHandlerFunc = default_exception_handler

        if client:
            self.add_to_client(client)

    def __repr__(self) -> str:
        return f"ComponentManager(name={self.name})"

    @property
    @typing_extensions.deprecated("Please use client instead.")
    def bot(self) -> disnake.Client:
        """An alias of :attr:`client`."""
        return self.client

    @property
    def client(self) -> disnake.Client:
        """The client to which this manager is registered.

        If the manager has not yet been registered, this raises an exception.

        .. note::
            This is recursively accessed for all the parents of this manager.
            For example, if ``get_manager().client`` is set, then any of its
            children ``get_manager("foo.bar").client`` will also return that
            same client instance.

            It is therefore generally recommended to set the client on the root
            manager so that all other managers automatically have access to it.
        """
        client = _recurse_parents_getattr(self, "_client", None)
        if client:
            return client

        msg = f"Component manager {self.name!r} is not yet registered to a client."
        raise RuntimeError(msg)

    @property
    def name(self) -> str:  # noqa: D102
        # <<docstring inherited from api.components.ComponentManager>>

        return self._name

    @property
    def children(self) -> set[ComponentManager]:  # noqa: D102
        # <<docstring inherited from api.components.ComponentManager>>

        return self._children

    @property
    def components(self) -> typing.Mapping[str, RichComponentType]:  # noqa: D102
        # <<docstring inherited from api.components.ComponentManager>>

        return self._components

    @property
    def count(self) -> bool:
        """Whether or not this manager should add a count character to custom ids.

        This prevents an error when two components with otherwise equal custom
        ids are sent.

        By default, this is set to :obj:`True`. This can be changed using
        :meth:`config`.

        .. note::
            This is recursively checked for all the parents of this manager.
            For example, if ``get_manager("foo").count == True``, then its
            child ``get_manager("foo.bar").count`` will also return ``True``
            unless explicitly set to ``False``.

        .. warning::
            As this takes 1 character, the effective maximum custom id length
            is reduced to 99 characters.
        """
        return _recurse_parents_getattr(self, "_count", _DEFAULT_COUNT)

    @property
    def counter(self) -> int:  # noqa: D102
        # <<docstring inherited from api.components.ComponentManager>>

        return self._counter

    @property
    def sep(self) -> str:
        """The separator used to delimit parts of the custom ids of this manager.

        By default, this is set to "|". This can be changed using
        :meth:`config`.

        .. note::
            This is recursively accessed for all the parents of this manager.
            For example, if ``get_manager("foo").sep == "|"``, then its
            child ``get_manager("foo.bar").sep`` will also return ``"|"``
            unless explicitly set to some other value.
        """
        return _recurse_parents_getattr(self, "_sep", _DEFAULT_SEP)

    @property
    def parent(self) -> ComponentManager | None:  # noqa: D102
        # <<docstring inherited from api.components.ComponentManager>>

        if "." not in self.name:
            # Return the root manager if this is not the root manager already.
            return None if self.name is _ROOT else get_manager(_ROOT)

        root, _ = self.name.rsplit(".", 1)
        return get_manager(root)

    def config(
        self,
        count: omit.OmittedNoneOr[bool] = omit.Omitted,
        sep: omit.OmittedNoneOr[str] = omit.Omitted,
    ) -> None:
        """Set configuration options on this manager."""
        if not omit.is_omitted(count):
            self._count = count

        if not omit.is_omitted(sep):
            self._sep = sep

    def make_identifier(self, component_type: RichComponentType) -> str:  # noqa: D102
        # <<docstring inherited from api.components.ComponentManager>>

        return component_type.__name__

    def get_identifier(  # noqa: D102
        self,
        custom_id: str,
    ) -> tuple[str, typing.Sequence[str]]:
        # <<docstring inherited from api.components.ComponentManager>>

        name, *params = custom_id.split(self.sep)

        if self.count and name.endswith(_COUNT_CHARS):
            # Count is always the single last character in the name part.
            return name[:-1], params

        return name, params

    def increment(self) -> str:  # noqa: D102
        count = _minimise_count(self._counter)

        self._counter += 1
        if self._counter > _MAX_COUNT:
            self._counter = 0

        return count

    async def make_custom_id(  # noqa: D102
        self,
        component: component_api.RichComponent,
    ) -> str:
        # <<docstring inherited from api.components.ComponentManager>>

        identifier = self._identifiers[type(component).__name__]

        if self.count:
            identifier = identifier + self.increment()

        dumped_params = await component.factory.dump_params(component)

        return self.sep.join([identifier, *dumped_params.values()])

    async def parse_message_interaction(  # noqa: D102
        self,
        interaction: disnake.Interaction[disnake.Client],
    ) -> component_api.RichComponent | None:
        # <<docstring inherited from api.components.ComponentManager>>
        if isinstance(interaction, disnake.MessageInteraction):
            return await self.parse_raw_component(interaction.component)

        raise NotImplementedError

    async def parse_raw_component(
        self,
        component: disnake.Button | disnake.BaseSelectMenu,
    ) -> component_api.RichComponent | None:
        """Parse a rich message component from a disnake raw component.

        .. note::
            This method only works for components registered to this manager.

        Parameters
        ----------
        component:
            The raw message component that is to be turned into a rich
            component.

        Returns
        -------
        :class:`RichComponent`
            The newly created component.
        :obj:`None`:
            The provided component could not be parsed into a rich component
            that is registered to this manager.

        """
        custom_id = component.custom_id
        if not custom_id:
            return None

        identifier, params = self.get_identifier(custom_id)

        if identifier not in self._components:
            return None

        component_type = self._components[identifier]
        module_data = self._module_data[identifier]

        if not module_data.is_active():
            # NOTE: This occurs if:
            #       - The module on which the component is defined was unloaded.
            #       - The module on which the component is defined was reloaded
            #         and the component was never overwritten. It could either
            #         have been removed, or simply no longer be registered. The
            #         component *should* therefore be unresponsive.
            #
            #       Since we do not want to fire components that (to the user)
            #       do not exist anymore, we should remove them from the
            #       manager and return None.
            self.deregister_component(component_type)
            return None

        component_params = {
            field.name: getattr(component, field.name)
            for field in fields.get_fields(
                component_type,
                kind=fields.FieldType.INTERNAL,
            )
        }

        return await component_type.factory.build_component(
            params,
            component_params=component_params,
        )

    async def parse_message_components(
        self,
        message: disnake.Message,
    ) -> tuple[
        typing.Sequence[typing.Sequence[MessageComponents]],
        typing.Sequence[component_api.RichComponent],
    ]:
        """Parse all components on a message into rich components or ui components.

        This method is particularly useful if you wish to modify multiple
        components attached to a given message.

        This returns a structure of components that can be directly passed into
        any send method's component parameters, and a separate sequence
        containing all rich components for easier editing.

        Parameters
        ----------
        message:
            The message of which to parse all components.

        Returns
        -------
        :class:`tuple`[:class:`Sequence`[:class:`Sequence`[:obj:`MessageComponents`]], :class:`Sequence`[:class:`RichComponent`]]
            A tuple containing:

            - A nested structure of sequences that contains the parsed message
            components. The outer sequence can contain a maximum of 5 inner
            sequences, which can each contain up to five components; as per
            Discord API spec.

            - A sequence containing only the rich components to facilitate
            easier modification of the components.

            These objects share the same component instances, so any changes
            made to components inside the separate sequence will also reflect
            on the nested structure.

        """  # noqa: E501
        new_rows: list[list[MessageComponents]] = []
        rich_components: list[component_api.RichComponent] = []

        current_component, current_component_id = _COMPONENT_CTX.get((None, None))
        should_test = current_component is not None

        for row in message.components:
            new_row: list[MessageComponents] = []
            new_rows.append(new_row)

            for component in row.children:
                if should_test and component.custom_id == current_component_id:
                    should_test = False
                    new_component = current_component

                else:
                    new_component = await self.parse_raw_component(component)

                if new_component:
                    rich_components.append(new_component)
                    assert isinstance(
                        new_component,
                        component_api.RichButton | component_api.RichSelect,
                    )

                else:
                    new_component = _to_ui_component(component)

                new_row.append(new_component)

        return new_rows, rich_components

    async def finalise_components(
        self,
        components: typing.Sequence[typing.Sequence[MessageComponents]],
    ) -> disnake.ui.Components[disnake.ui.MessageUIComponent]:
        """Finalise the output of :meth:`parse_message_components` back into disnake ui components.

        Parameters
        ----------
        components:
            A sequence of rows of components, which can be any combination of
            disnake ui components and rich components. The rich components are
            automatically cast to their equivalent disnake ui components so
            that they can be sent as an interaction response.

        Returns
        -------
        disnake.ui.Components[disnake.ui.MessageUIComponent]:
            A disnake-compatible structure of sendable components.

        """
        finalised: list[list[disnake.ui.MessageUIComponent]] = []

        for row in components:
            new_row: list[disnake.ui.MessageUIComponent] = []
            finalised.append(new_row)

            for component in row:
                if isinstance(component, component_api.RichButton | component_api.RichSelect):
                    new_row.append(await component.as_ui_component())  # pyright: ignore[reportArgumentType]
                else:
                    new_row.append(component)

        return finalised

    # Identifier and component: function call, return component
    @typing.overload
    def register(
        self,
        component_type: type[RichComponentT],
        *,
        identifier: str | None = None,
    ) -> type[RichComponentT]: ...

    # Only identifier: nested decorator, return callable that registers and
    # returns the component.
    @typing.overload
    def register(
        self,
        *,
        identifier: str | None = None,
    ) -> typing.Callable[[type[RichComponentT]], type[RichComponentT]]: ...

    def register(
        self,
        component_type: type[RichComponentT] | None = None,
        *,
        identifier: str | None = None,
    ) -> type[RichComponentT] | typing.Callable[[type[RichComponentT]], type[RichComponentT]]:
        """Register a component to this component manager.

        This is the decorator interface to :meth:`register_component`.
        """
        if component_type is not None:
            return self.register_component(component_type, identifier=identifier)

        def wrapper(
            component_type: type[RichComponentT],
        ) -> type[RichComponentT]:
            return self.register_component(component_type, identifier=identifier)

        return wrapper

    def register_component(  # noqa: D102
        self,
        component_type: type[RichComponentT],
        *,
        identifier: str | None = None,
    ) -> type[RichComponentT]:
        # <<docstring inherited from api.components.ComponentManager>>
        resolved_identifier = identifier or self.make_identifier(component_type)
        module_data = _ModuleData.from_object(component_type)

        root_manager = get_manager(_ROOT)

        if resolved_identifier in root_manager._components:  # noqa: SLF001
            # NOTE: This occurs when a component is registered while another
            #       component with the same identifier already exists.
            #
            #       We now have two options:
            #       - This is caused by a reload. In this case, we expect the
            #         module name to remain unchanged and the module id to have
            #         changed. We can safely overwrite the old component.
            #       - This is an actual user error. If we were to silently
            #         overwrite the old component, it would unexpectedly go
            #         unresponsive. Instead, we raise an exception to the user.
            old_module_data = root_manager._module_data[resolved_identifier]  # noqa: SLF001
            if not module_data.is_reload_of(old_module_data):
                message = (
                    "Cannot register component with duplicate identifier"
                    f" {identifier!r}. (Original defined in module"
                    f" {old_module_data.name!r}, duplicate defined in module"
                    f" {module_data.name!r})"
                )
                raise RuntimeError(message)

        # Register to current manager and all parent managers.
        component_type.manager = self

        for manager in _recurse_parents(self):
            manager._components[resolved_identifier] = component_type  # noqa: SLF001
            manager._identifiers[component_type.__name__] = resolved_identifier  # noqa: SLF001
            manager._module_data[resolved_identifier] = module_data  # noqa: SLF001

        return component_type

    def deregister_component(  # noqa: D102
        self,
        component_type: RichComponentType,
    ) -> None:
        # <<docstring inherited from api.components.ComponentManager>>

        identifier = self.make_identifier(component_type)
        component = self._components[identifier]

        if not component.manager:
            message = (
                f"Component {component_type.__name__!r} is not registered to a component manager."
            )
            raise TypeError(message)

        if not isinstance(component.manager, ComponentManager):
            # This should honestly never happen unless the user does some
            # really weird stuff.
            # TODO: Maybe think of an error message for this.
            raise TypeError

        # Deregister from the current manager and all parent managers.
        for manager in _recurse_parents(component.manager):
            manager._components.pop(identifier)  # noqa: SLF001
            manager._module_data.pop(identifier)  # noqa: SLF001

    def add_to_client(self, client: disnake.Client, /) -> None:  # noqa: D102
        # <<docstring inherited from api.components.ComponentManager>>

        # Ensure we don't duplicate the listeners.
        if (
            self.invoke_component in client.extra_events.get(_COMPONENT_EVENT, [])
            # or self.invoke_component in client.extra_events.get(_MODAL_EVENT, [])
        ):  # fmt: skip
            message = "This component manager is already registered to this client."
            raise RuntimeError(message)

        client.add_listener(self.invoke_component, _COMPONENT_EVENT)
        # client.add_listener(self.invoke, _MODAL_EVENT)  # noqa: ERA001

        self._client = client

    @typing_extensions.deprecated("Please use add_to_client() instead.")
    def add_to_bot(self, bot: disnake.Client) -> None:  # noqa: D102
        self.add_to_client(bot)

    def remove_from_client(self, client: disnake.Client, /) -> None:  # noqa: D102
        # <<docstring inherited from api.components.ComponentManager>>

        # client.remove_listener silently ignores if the event doesn't exist,
        # so we manually handle raising an exception for it.
        if not (
            self.invoke_component in client.extra_events.get(_COMPONENT_EVENT, [])  # noqa: E713
            # and self.invoke_component in client.extra_events.get(_MODAL_EVENT, [])
        ):  # fmt: skip
            message = "This component manager is not yet registered to this client."
            raise RuntimeError(message)

        client.remove_listener(self.invoke_component, _COMPONENT_EVENT)
        # client.remove_listener(self.invoke_component, _MODAL_EVENT)  # noqa: ERA001

    @typing_extensions.deprecated("Please use remove_from_client() instead.")
    def remove_from_bot(self, bot: disnake.Client) -> None:  # noqa: D102
        self.remove_from_client(bot)

    def as_dependency_provider(self, func: DependencyProviderFuncT) -> DependencyProviderFuncT:
        """Register a callback as this manager's dependency provider.

        By default, this registers everything passed as a dependency.

        A dependency provider MUST be an async function with ONE yield statement.
        - Any code before the yield statement is run before the interaction is
        parsed,
        - The interaction is parsed at the yield statement,
        - Any code after the yield statement is run after the interaction has
        been parsed. This can be used for cleanup.

        It is therefore also possible to use context managers over the yield
        statement, to automatically handle resource management.

        As this runs *before* we know which manager a component belongs to (if
        at all!), this is run only for the manager(s) registered to a client
        with :meth:`add_to_client`.

        Examples
        --------
        .. code-block:: python

            manager = get_manager()


            @manager.as_dependency_provider
            async def provider(manager, *dependencies):
                tokens = di.register_dependencies(*dependencies)
                yield
                di.reset_dependencies(tokens)

        Parameters
        ----------
        func:
            The callback to register. This must be an async function that takes
            the component manager as the first argument, and any number of
            dependencies after. The function must have a single ``yield``
            statement that yields ``None``.

        Returns
        -------
        Callable[[:class:`ComponentManager`, ...], AsyncGenerator[None, None]]
            The function that was just registered.

        """
        self.set_invocation_dependencies = contextlib.asynccontextmanager(func)
        return func

    def as_callback_wrapper(self, func: CallbackWrapperFuncT) -> CallbackWrapperFuncT:
        """Register a callback as this managers' callback wrapper.

        By default, this is essentially a no-op.

        A callback wrapper MUST be an async function with ONE yield statement.
        - Any code before the yield statement is run before the component
        callback is invoked,
        - The component is invoked at the yield statement,
        - Any code after the yield statement is run after the component
        callback is invoked. This can be used for cleanup.

        It is therefore also possible to use context managers over the yield
        statement, to automatically handle resource management.

        In case this manager has a parent manager, the parent's callback
        wrapper will be used first, starting all the way at the root manager.
        For example, on a manager named "foo.bar", the callback will first be
        wrapped by the root manager, then by "foo", then by "foo.bar", and only
        then will the component callback finally be invoked.

        Note that any exceptions raised in any callback wrapper will cancel any
        other active callback wrappers and propagate the exception to the
        manager's error handler.

        Examples
        --------
        .. code-block:: python

            manager = get_manager()


            @manager.as_callback_wrapper
            async def wrapper(component, interaction):
                print(f"User {inter.author.name} invoked {type(component).__name__}.)
                yield
                print(f"Successfully ran callback for {type(component).__name__}.)

        Parameters
        ----------
        func:
            The callback to register. This must be an async function that takes
            the component manager as the first argument, the component as the
            second argument, and the interaction as the last. The function must
            have a single ``yield``-statement that yields ``None``.

        Returns
        -------
        Callable[[:class:`RichComponent`, :class:`disnake.Interaction[disnake.Client]`], AsyncGenerator[None, None]]
            The function that was just registered.

        """  # noqa: E501
        self.wrap_callback = contextlib.asynccontextmanager(func)
        return func

    def as_exception_handler(
        self,
        func: ExceptionHandlerFuncT,
    ) -> ExceptionHandlerFuncT:
        """Register a callback as this managers' error handler.

        By default, this simply logs the exception and keeps it from
        propagating.

        An error handler should return a boolean or ``None``:
        - ``True`` if the error was successfully handled and should not be
        propagated further.
        - ``False`` or ``None`` if the error was *not* successfully handled and
        should be passed to the next error handler in line.

        Note that it is therefore also possible to use context managers over
        the yield statement.

        In case this manager has a parent manager, the parent's error handler
        will be used if this one returns ``False`` or ``None``. For example,
        of a manager named "foo.bar", any exceptions will first be handled by
        "foo.bar", if that fails it will be handled by "foo", and finally if
        that also fails it will be handled by the root handler.

        Examples
        --------
        .. code-block:: python

            manager = get_manager()


            @manager.as_exception_handler
            async def wrapper(component, interaction, exception):
                if isinstance(exception, TypeError):
                    return True  # Silently ignore any TypeErrors

                return False  # Propagate all other errors.

        Parameters
        ----------
        func:
            The callback to register. This must be an async function that takes
            the component manager as the first argument, the component as the
            second, the interaction as the third, and the exception as the last.
            The function must return ``True`` to indicate that the error was
            handled successfully, or either ``False`` or ``None`` to indicate
            the opposite.

        Returns
        -------
        Callable[[:class:`RichComponent`, :class:`disnake.Interaction[disnake.Client]`, :class:`Exception`], None]
            The function that was just registered.

        """  # noqa: E501
        self.handle_exception = func
        return func

    async def _invoke_component(
        self,
        interaction: disnake.MessageInteraction[disnake.Client],
        /,
    ) -> None:
        # First, we check if the component is managed.
        component = await self.parse_message_interaction(interaction)
        if not (component and component.manager):
            # If the component was found, the manager is guaranteed to be
            # defined but we need the extra check for type-safety.
            return

        if not isinstance(component.manager, ComponentManager):
            # This should honestly never happen unless the user does some
            # really weird stuff.
            # TODO: Maybe think of an error message for this.
            raise TypeError

        # We traverse the managers in reverse: root first, then child, etc.
        # until we reach the component's actual manager. Therefore, we first
        # store all managers in a list, so that we can call reversed() on it
        # later.
        # This applies only to the callback wrappers. Error handlers are called
        # starting from the actual manager and propagated down to the root
        # manager if the error was left unhandled.
        managers = list(_recurse_parents(component.manager))

        assert interaction.component.custom_id
        ctx_value = (component, interaction.component.custom_id)
        component_ctx_token = _COMPONENT_CTX.set(ctx_value)

        try:
            async with contextlib.AsyncExitStack() as stack:
                # Enter all the context managers...
                for manager in reversed(managers):
                    await stack.enter_async_context(
                        manager.wrap_callback(manager, component, interaction),
                    )

                # If none raised, we run the callback.
                await component.callback(interaction)

        except Exception as exception:  # noqa: BLE001
            # Blanket exception catching is desired here as it's meant to
            # redirect all non-system errors to the error handler.

            for manager in managers:
                if await manager.handle_exception(
                    manager,
                    component,
                    interaction,
                    exception,
                ):
                    # If an error handler returns True, consider the error
                    # handled and skip the remaining handlers.
                    break

        finally:
            _COMPONENT_CTX.reset(component_ctx_token)

    async def invoke_component(  # noqa: D102
        self,
        interaction: disnake.MessageInteraction[disnake.Client],
        /,
        *,
        with_di: bool = True,
    ) -> None:
        # <<docstring inherited from api.components.ComponentManager>>

        if with_di:
            async with self.set_invocation_dependencies(
                self,
                interaction,
                interaction.guild,
                interaction.bot,
                interaction.channel,
                interaction.author,
                # XXX:  Potential edge-case here where a parser needs a user
                #       but we can only provide a member.
            ):
                await self._invoke_component(interaction)

        else:
            await self._invoke_component(interaction)

    def make_button(  # noqa: PLR0913
        self,
        identifier: str,
        *,
        as_root: bool = True,
        label: omit.Omissible[str | None] = omit.Omitted,
        style: omit.Omissible[disnake.ButtonStyle] = omit.Omitted,
        emoji: omit.Omissible[component_api.AnyEmoji | None] = omit.Omitted,
        disabled: omit.Omissible[bool] = omit.Omitted,
        **kwargs: object,
    ) -> component_api.RichButton:
        """Make an instance of the button class with the provided identifier.

        Parameters
        ----------
        as_root:
            Whether to use the root manager to get the component. This defaults
            to ``True`` so that any externally registered button can be built.
        identifier:
            The identifier of the button that is to be instantiated.
        label:
            The label to use. If not provided, uses the button class' default.
        style: disnake.ButtonStyle
            The style to use. If not provided, uses the button class' default.
        emoji:
            The emoji to use. If not provided, uses the button class' default.
        disabled:
            Whether or not to disable the button. If not provided, uses the
            button class' default.
        **kwargs:
            Any remaining keyword arguments are passed to the button's ``__init__``.

        Returns
        -------
        :class:`disnake_compass.api.RichButton`
            The newly created button.

        Raises
        ------
        :class:`KeyError`
            The provided identifier does not belong to a registered component.
        :class:`TypeError`
            The provided identifier belongs to a component that is not a button.
        :class:`Exception`
            Any exception raised during button instantiation is propagated as-is.

        """
        if label is not omit.Omitted:
            kwargs["label"] = label
        if style is not omit.Omitted:
            kwargs["style"] = style
        if emoji is not omit.Omitted:
            kwargs["emoji"] = emoji
        if disabled is not omit.Omitted:
            kwargs["disabled"] = disabled

        manager = get_manager(_ROOT) if as_root else self
        component_type = manager.components[identifier]
        component = component_type(**kwargs)

        # NOTE: We sadly cannot use issubclass-- maybe make a custom issubclass
        #       implementation that works with protocols with non-method members
        #       given a couple assumptions.
        if isinstance(component, component_api.RichButton):
            return component

        msg = (
            f"Expected identifier {identifier!r} to point to a button class,"
            f" got {component_type.__name__}."
        )
        raise TypeError(msg)

    def make_select(  # noqa: PLR0913
        self,
        identifier: str,
        *,
        as_root: bool = True,
        placeholder: omit.Omissible[str | None] = omit.Omitted,
        min_values: omit.Omissible[int] = omit.Omitted,
        max_values: omit.Omissible[int] = omit.Omitted,
        disabled: omit.Omissible[bool] = omit.Omitted,
        options: omit.Omissible[list[disnake.SelectOption]] = omit.Omitted,
        **kwargs: object,
    ) -> component_api.RichSelect:
        """Make an instance of the string select class with the provided identifier.

        Parameters
        ----------
        as_root:
            Whether to use the root manager to get the component. This defaults
            to ``True`` so that any externally registered select can be built.
        identifier:
            The identifier of the button that is to be instantiated.
        placeholder:
            The placeholder to use. If not provided, uses the select class' default.
        min_values:
            The minimum number of values a user is allowed to select. If not
            provided, uses the select class' default.
        max_values:
            The maximum number of values a user is allowed to select. If not
            provided, uses the select class' default.
        disabled:
            Whether or not to disable the button. If not provided, uses the
            select class' default.
        options:
            The options to use. If not provided, uses the select class' default.
        **kwargs:
            Any remaining keyword arguments are passed to the select's ``__init__``.

        Returns
        -------
        :class:`disnake_compass.api.RichStringSelect`
            The newly created string select.

        Raises
        ------
        :class:`KeyError`
            The provided identifier does not belong to a registered component.
        :class:`TypeError`
            The provided identifier belongs to a component that is not a string select.
        :class:`Exception`
            Any exception raised during button instantiation is propagated as-is.

        """
        # NOTE: This currently only supports StringSelects

        if placeholder is not omit.Omitted:
            kwargs["placeholder"] = placeholder
        if min_values is not omit.Omitted:
            kwargs["min_values"] = min_values
        if max_values is not omit.Omitted:
            kwargs["max_values"] = max_values
        if disabled is not omit.Omitted:
            kwargs["disabled"] = disabled
        if options is not omit.Omitted:
            kwargs["options"] = options

        manager = get_manager(_ROOT) if as_root else self
        component_type = manager.components[identifier]
        component = component_type(**kwargs)

        # NOTE: We sadly cannot use issubclass-- maybe make a custom issubclass
        #       implementation that works with protocols with non-method members
        #       given a couple assumptions.
        if isinstance(component, component_api.RichSelect):
            return component

        msg = (
            f"Expected identifier {identifier!r} to point to a select class,"
            f" got {component_type.__name__}."
        )
        raise TypeError(msg)


_MANAGER_STORE: typing.Final[dict[str, ComponentManager]] = {}


def _recurse_parents(manager: ComponentManager) -> typing.Iterator[ComponentManager]:
    yield manager
    while manager := manager.parent:  # pyright: ignore[reportAssignmentType]
        yield manager


def _recurse_parents_getattr(
    manager: ComponentManager,
    attribute: str,
    default: T,
) -> T:
    for parent in _recurse_parents(manager):
        value = getattr(parent, attribute)
        if value is not None:
            return value

    return default


def get_manager(name: str | None = None) -> ComponentManager:
    """Get a manager by name, or create one if it does not yet exist.

    Calling :func:`get_manager` without specifying a name returns the root
    manager. The root manager is -- unless explicitly modified by the user --
    guaranteed to be the lowest-level manager, with no parents.

    Managers follow a parent-child hierarchy. For example, a manager "foo.bar"
    would be a child of "foo". Any components registered to "foo.bar" would
    also be accessible to manager "foo". This means that the root manager
    has access to all components.

    To register a component to a manager, use :meth:`ComponentManager.register`.
    To ensure component callbacks are invoked, the manager must first be linked
    to a client. This is done using :meth:`ComponentManager.add_to_client`.
    Since parents have access to the components of their children, it is often
    sufficient to bind only the root manager to a client.

    It is generally recommended to use a separate manager per extension, though
    you can share the same manager between files by using the same name, if
    desired.

    Further configuration of managers can be done through
    :meth:`ComponentManager.config`.

    Parameters
    ----------
    name: str
        The name of the component. If not provided, the root manager is
        returned.

    Returns
    -------
    :class:`ComponentManager`:
        A component manager with the desired name. If a component manager with
        this name already existed before calling this function, that same
        manager is returned. Otherwise, a new manager is created.

    """
    if name is None:
        # TODO: Maybe use a sentinel:
        #       - auto-infer name if sentinel,
        #       - return root logger if None was passed explicitly.
        name = _ROOT

    if name in _MANAGER_STORE:
        return _MANAGER_STORE[name]

    _MANAGER_STORE[name] = manager = ComponentManager(name)

    if "." in name:
        root, _ = name.rsplit(".", 1)
        parent = get_manager(root)
        parent.children.add(manager)

    return manager


def check_manager(name: str) -> bool:
    """Check if a manager with the provided name exists.

    .. note::
        Unlike :func:`get_manager`, this function will not create a manager
        if the provided name does not exist.

    Parameters
    ----------
    name:
        The name to check.

    Returns
    -------
    :class:`bool`
        Whether a manager with the provided name exists.

    """
    return name in _MANAGER_STORE
