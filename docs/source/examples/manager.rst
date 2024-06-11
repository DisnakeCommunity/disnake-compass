.. currentmodule:: disnake-ext-components

Component Manager
=================

A simple example on the use of component managers with disnake-ext-components.


First and foremost, we create a bot as per usual. Since we don't need any
prefix command capabilities, we opt for an :class:`~disnake.ext.commands.InteractionBot`.

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - creating a Bot object
    :lines: 3-9


Next, we create a component manager.

A call to :func:`.get_manager` without arguments returns the root manager.
We register the root manager to the bot, which will ensure all components we register to any other manager will automatically be handled. This is because a manager handles its own components along with any of its children's.

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - create a root component manager
    :lines: 11-12
    :emphasize-lines: 1


We can create a child manager as follows

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - create a child manager
    :lines: 14


We can go deeper in the parent/child hierarchy by separating them with dots

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - create a deeply nested manager
    :lines: 15

.. note::
    Any missing bits will automatically be filled in-- the above line has automatically created a manager named "foo.bar", too.


Now let us quickly register a button each to our ``foo_manager`` and our ``deeply_nested_manager``. To this end, we will use the :ref:`button example <button example>`

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - creating a button component
    :lines: 18-41


Customizing your component manager
----------------------------------

For most use cases, the default implementation of the component manager should suffice. Two methods of interest to customise your managers without having to subclass them are :meth:`ComponentManager.as_callback_wrapper` and :meth:`ComponentManager.as_error_handler`.

:meth:`ComponentManager.as_callback_wrapper` wraps the callbacks of all components registered to that manager along with those of its children. Therefore, if we were to add a callback wrapper to the root manager, we would ensure it applies to *all* components. For example, say we want to log all component interactions

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - customizing your component manager
    :lines: 44-60
    :emphasize-lines: 1-6, 12

.. tip::
    For actual production code, please use logging instead of print.

Any code placed after the yield statement runs after the component callback is invoked. This can be used for cleanup of resources

.. note::
    Any changes made to the component instance by other wrappers and/or the callback itself are reflected here.


This feature can also be used as a check. By raising an exception before the component callback is invoked, you can prevent it from being invoked entirely. The exception is then also passed to exception handlers.

For example, let's allow *only* the original slash command author to interact with any components on this manager.

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - creating a check to prevent the component callback call
    :lines: 63-84
    :emphasize-lines: 8-13, 20, 22
    :linenos:

Now in our custom check we adds some logic to filter out who should be able to use our component:

This check only applies to message interactions (*line 15*)...
The message must have been sent as interaction response (*line 16*)...
The component user is **NOT** the same as the original interaction user (*line 17*)...

If all the conditions are satisfied we raise our custom error for convenience (*lines 19-20*).


Similarly, we can create an exception handler for our components. An exception handler function should return ``True`` if the error was handled, and ``False`` or ``None`` otherwise.
The default implementation hands the exception down to the next handler until it either is handled or reaches the root manager. If the root manager is reached (and does not have a custom exception handler), the exception is logged.

To demonstrate the difference, we will make a custom error handler only for the ``deeply_nested_manager``.

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - components custom error handler
    :lines: 87-99
    :emphasize-lines: 1-7, 11, 13

.. note::
    You do not need to explicitly return ``False``. Returning ``None`` is sufficient. Explicitly returning ``False`` is simply preferred for clarity.

Finally, we send the components to test the managers.

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - sending the components
    :lines: 102-115

Lastly, we run the bot.

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py - running the bot
    :lines: 118

Source Code
-----------

.. literalinclude:: ../../../examples/manager.py
    :caption: examples/manager.py
    :lines: 3-118
    :emphasize-lines: 9-10, 12-13, 42-47, 53, 68-73, 80, 82, 85-91, 95, 97
    :linenos:
