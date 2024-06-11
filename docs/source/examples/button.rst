Button
======
A simple example on the use of buttons with disnake-ext-components.


First and foremost, we create a bot as per usual. Since we don't need any
prefix command capabilities, we opt for an :class:`~disnake.ext.commands.InteractionBot`.

.. literalinclude:: ../../../examples/button.py
    :caption: examples/button.py - create a Bot object
    :lines: 3-8

Next, we make a component manager and register it to the bot.

.. literalinclude:: ../../../examples/button.py
    :caption: examples/button.py - create a component manager and registering it
    :lines: 10-11

Then we make a simple component and register it to the manager.
This component is a button that increments its label each time it is clicked.

.. _button example:

.. literalinclude:: ../../../examples/button.py
    :caption: examples/button.py - create a component
    :lines: 14-24
    :emphasize-lines: 1

Set the ``label`` of the button...

.. literalinclude:: ../../../examples/button.py
    :lines: 16

Define a ``custom_id`` parameter...

.. literalinclude:: ../../../examples/button.py
    :lines: 18

Then in the callback we increment the count, update the label to match the count and update our component.

.. literalinclude:: ../../../examples/button.py
    :lines: 20-24


Finally, we make a command that sends the component.

.. literalinclude:: ../../../examples/button.py
    :caption: examples/button.py - create a command and send the component
    :lines: 28-32
    :emphasize-lines: 2, 5

.. tip::
    Wrapping the interaction allows you to send the component as-is.

    If we had not wrapped the interaction, we would have needed to do ``await inter.send(components=await component.as_ui_component())`` instead.

Lastly, we run the bot.

.. literalinclude:: ../../../examples/button.py
    :lines: 35

Source code
-----------

.. literalinclude:: ../../../examples/button.py
    :caption: examples/button.py
    :start-at: import os
    :lines: 1-33
    :emphasize-lines: 8-9, 12, 27, 30
    :linenos:
