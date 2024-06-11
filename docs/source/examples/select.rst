Select
======
A simple example on the use of selects with disnake-ext-components.

For this example, we implement a select menu with double functionality.
Firstly, the select allows you to select one of three slots. After selecting a
slot, the select is modified to instead allow you to select a colour. The
selected slot and colour are then combined to colour the corresponding square.


First and foremost, we create a bot as per usual. Since we don't need any
prefix command capabilities, we opt for an :class:`~disnake.ext.commands.InteractionBot`.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - creating a Bot object
    :lines: 9-17


Next, we make a component manager and register it to the bot.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - creating a manager and registering it
    :lines: 19-20


Define possible slots for our select.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - defining slots
    :lines: 23-32


Define possible colours for our select.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - defining colours
    :lines: 35-53


Then, we make and register the select.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - creating a select component
    :lines: 56-99
    :emphasize-lines: 1, 6-10
    :linenos:

Set the placeholder text (*line 3*)...
Set the options (*line 4*)...
We store the slot the user is currently working with (*line 6*)...
We store whether they're picking a slot or a colour (*line 7*)...
And we store the colours for the three slots (*lines 63-65*)...

In the callback first we get the selected value.

This should never raise for a select.

.. literalinclude:: ../../../examples/select.py
    :lines: 67-78
    :linenos:

If the selection was a slot, run slot selection logic (*lines 5-6*).
To keep things tidy, we use a separate function for this.
Otherwise, run colour selection logic (*lines 8-9*).
Finally we render the new colours and update the select (*lines 77-78*).

Then in ``handle_slots``:

.. literalinclude:: ../../../examples/select.py
    :lines: 80-90
    :linenos:

In case the user wishes to finalize, disable the select (*lines 2-5*).
Update options and display (*lines 7-8*).
Set the slot to the user's selection and set state to colour (*lines 10-11*).

Then in ``handle_colours``:

.. literalinclude:: ../../../examples/select.py
    :lines: 92-96

Update the options set the corresponding colour attribute and set state to slot.

Then in ``render_colours``:

.. literalinclude:: ../../../examples/select.py
    :lines: 98-99

Render our three squares.


Finally, we make a command that sends the component.
In this command, we initialise the timeout for the component.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - sending the component
    :lines: 102-109
    :emphasize-lines: 3, 6-8

.. tip::
    Wrapping the interaction allows you to send the component as-is.

    If we had not wrapped the interaction, we would have needed to do ``await inter.send(components=await component.as_ui_component())`` instead.

Lastly, we run the bot.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - running the bot
    :lines: 112

Source Code
-----------

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py
    :lines: 9-112
    :emphasize-lines: 11-12, 48, 53-57, 96, 99-101, 104
    :linenos:
