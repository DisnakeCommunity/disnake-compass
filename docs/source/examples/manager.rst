.. currentmodule:: disnake-compass

Component Manager
=================

Step-by-Step
------------

A simple example on the use of component managers with disnake-compass.

First, we create a new component manager.
A call to :func:`.get_manager` without arguments returns the root manager. You can think of this in much the same way as :py:func:`logging.getLogger`.
A manager handles components registered to itself and any of its children.
To make sure a bot can actually interact with the manager, we must register the bot to the manager.

.. literalinclude:: ../../../examples/manager.py
    :name: create-root-manager
    :caption: examples/manager.py - create root manager
    :lines: 9,11-12

We can create a child manager by entering a name into :func:`.get_manager`, the returned manager will be a child of the root manager. Again similar to :py:func:`logging.getLogger`, we can create a complex parent-child hierarchy by using dot-qualified names.

.. literalinclude:: ../../../examples/manager.py
    :name: create-a-child-manager
    :caption: examples/manager.py - create child manager
    :lines: 14-15

.. note::
    Any missing bits will automatically be filled in-- the above snippet has implicitly created a manager named "foo.bar".

To register a component to a manager, we use :func:`ComponentManager.register() <components.impl.manager.ComponentManager.register>`.
For purposes that will become clear in the later on in this example, we will register a component to both our ``foo_manager`` and our ``deeply_nested_manager``.
To this end, we will use the :doc:`button example </examples/button>` as simple components to work with.
Since we will need it later, we immediately add a command to send each button.

.. literalinclude:: ../../../examples/manager.py
    :name: register-components
    :caption: examples/manager.py - register components
    :lines: 18-43, 102-115


Customizing your component manager
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For most use cases, the default implementation of the component manager should suffice.
Two methods of interest to customise your managers without having to subclass them are :func:`ComponentManager.as_callback_wrapper() <components.impl.manager.ComponentManager.as_callback_wrapper>` and :func:`ComponentManager.as_exception_handler() <components.impl.manager.ComponentManager.as_exception_handler>`.


Callback Wrappers
"""""""""""""""""
A callback wrapper is essentially a :func:`context mananger <contextlib.contextmanager>`. In short, this is a function that does some setup, yields to let the "managed" callback run, and then gets to do something again after the callback finished running. Callback wrappers, like context managers, can be nested.

:func:`ComponentManager.as_callback_wrapper() <components.impl.manager.ComponentManager.as_callback_wrapper>` wraps the callbacks of all components registered to that manager along with those of its children. Therefore, if we were to add a callback wrapper to the root manager, we would ensure it applies to *all* components. For example, say we want to log all component interactions:

.. literalinclude:: ../../../examples/manager.py
    :name: creating-a-logging-wrapper
    :caption: examples/manager.py - creating a logging wrapper
    :lines: 44-60
    :emphasize-lines: 12
    :linenos:

.. tip::
    For actual production code, consider using logging instead of print.

This creates a wrapper that prints who interacted with the component (*lines 7-10*),
lets the component run (*line 12*),
and finally prints that the component interaction was successful (*lines 14-17*).

.. note::
    Anything after the yield is ignored if the callback raised an error, **unless** the yield is wrapped in a ``try-except`` block.
    This works in the same way as normal contextmanagers would.

This feature can also be used as a check.
By raising an exception before the component callback is invoked, you can prevent it from being invoked entirely.
The exception is then also passed to exception handlers.
For example, we create a wrapper that allows only the original slash command author to interact with any components on this manager.

.. literalinclude:: ../../../examples/manager.py
    :name: creating-a-check
    :caption: examples/manager.py - creating a check
    :lines: 63-84
    :emphasize-lines: 14-20
    :linenos:

This callback wrapper contains a check that only fires for message interactions (*line 15*),
where the message must have been sent as interaction response (*line 16*),
and the component user is **NOT** the same as the original interaction user (*line 17*).
If all the conditions are satisfied we raise a custom error for convenience (*lines 19-20*),
otherwise, we yield to the wrapped callback (*line 22*).

.. note::
    All component wrappers receive the component instance as-is.
    This means that any modifications done to the component are reflected inside other wrappers and the wrapped callback itself.


Exception handlers
""""""""""""""""""

Similarly, we can create an exception handler for our components using :func:`ComponentManager.as_exception_handler() <components.impl.manager.ComponentManager.as_exception_handler>`. An exception handler function should return :obj:`True` if the error was handled, and :obj:`False` or :obj:`None` otherwise.

The default implementation hands the exception down to the next handler until it either is handled or reaches the root manager.
If the root manager is reached (and does not have a custom exception handler), the exception is logged.

To demonstrate this, we will make a custom error handler only for the ``deeply_nested_manager``.
Consider the previously established :ref:`user check wrapper <creating-a-check>`.
We raised a custom exception there, and we wish to handle it in this exception handler.

.. literalinclude:: ../../../examples/manager.py
    :name: creating-an-exception-handler
    :caption: examples/manager.py - creating an exception handler
    :lines: 87-99
    :emphasize-lines: 11, 13

.. note::
    You do not need to explicitly return ``False``. Returning ``None`` -- and thus a blank ``return`` statement -- is sufficient.
    Explicitly returning ``False`` is simply preferred for clarity.

Using the components and commands registered in the :ref:`register components codeblock <register-components>` combined with the :ref:`logging wrapper <creating-a-logging-wrapper>` and the :ref:`user check wrapper <creating-a-check>`, we can assess the following four cases:

1. *User A* uses ``/test_button`` and *User A* clicks the resulting button,
2. *User A* uses ``/test_button`` and *User B* clicks the resulting button,
3. *User A* uses ``/test_nested_button`` and *User A* clicks the resulting button,
4. *User A* uses ``/test_nested_button`` and *User B* clicks the resulting button.

.. tab:: Case 1

    The invoked command is ``/test_button``, so the button in question is a ``FooButton``, which is registered to the ``foo_manager``.
    This manager does not have a callback wrapper registered to it.
    However, the root manager has the :ref:`logging wrapper <creating-a-logging-wrapper>`.

    As the button is invoked, the following mechanisms are triggered in order:

    1. The :ref:`logging wrapper <creating-a-logging-wrapper>` logs the attempted invocation;
    2. The component callback is executed successfully;
    3. The :ref:`user check wrapper <creating-a-check>` does not do anything after the component finishes;

.. tab:: Case 2

    The invoked command is ``/test_button``, so the button in question is a ``FooButton``, which is registered to the ``foo_manager``.
    This manager does not have a callback wrapper registered to it.
    However, the root manager has the :ref:`logging wrapper <creating-a-logging-wrapper>`.

    As the button is invoked, the following mechanisms are triggered in order:

    1. The :ref:`logging wrapper <creating-a-logging-wrapper>` logs the attempted invocation;
    2. The component callback is executed successfully;
    3. The :ref:`user check wrapper <creating-a-check>` does not do anything after the component finishes;

    .. tip::
        As ``foo_manager`` does not see the callback wrapper registered to ``deeply_nested_manager``, it's irrelevant who clicked the button, as the check simply doesn't apply.


.. tab:: Case 3

    The invoked command is ``/test_nested_button``, so the button in question is a ``FooBarBazButton``, which is registered to the ``deeply_nested_manager``.
    This manager has the :ref:`user check wrapper <creating-a-check>` registered to it.
    Furthermore, the root manager has the :ref:`logging wrapper <creating-a-logging-wrapper>`.

    As the button is invoked, the following mechanisms are triggered in order:

    1. The :ref:`logging wrapper <creating-a-logging-wrapper>` logs the attempted invocation;
    2. The :ref:`user check wrapper <creating-a-check>` passes because the user clicking the button (*User A*) is the original command author (*User A*);
    3. The component callback is executed successfully;
    4. The :ref:`user check wrapper <creating-a-check>` does not do anything after the component finishes;
    5. The :ref:`logging wrapper <creating-a-logging-wrapper>` logs the successful invocation of the component.

.. tab:: Case 4

    The invoked command is ``/test_nested_button``, so the button in question is a ``FooBarBazButton``, which is registered to the ``deeply_nested_manager``.
    This manager has the :ref:`user check wrapper <creating-a-check>` registered to it.
    Furthermore, the root manager has the :ref:`logging wrapper <creating-a-logging-wrapper>`.

    As the button is invoked, the following mechanisms are triggered in order:

    1. The :ref:`logging wrapper <creating-a-logging-wrapper>` logs the attempted invocation;
    2. The :ref:`user check wrapper <creating-a-check>` fails because the user clicking the button (*User A*) is **NOT** the original command author (*User B*).
       An ``InvalidUserError`` is raised;
    3. The component callback is **NOT** executed;
    4. The :ref:`user check wrapper <creating-a-check>` does not not get to continue running;
    5. The :ref:`logging wrapper <creating-a-logging-wrapper>` does not get to continue running;
    6. The :ref:`exception handler <creating-an-exception-handler>` catches the ``InvalidUserError`` and returns True.
       The exception is deemed successfully handled, and no further handlers are triggered.


.. important::
    Callback wrappers are traversed from the root manager down to the child that invokes the component.

    Exception handlers are traversed in reverse order: from the child down to the root manager.


Source Code
-----------
:example:`manager`

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py
    :linenos:
