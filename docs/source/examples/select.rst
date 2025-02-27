Select
======

Step-by-Step
------------

A simple example on the use of selects with disnake-compass.

For this example, we implement a select menu with double functionality.
Firstly, the select allows you to select one of three slots. After selecting a
slot, the select is modified to instead allow you to select a colour. The
selected slot and colour are then combined to colour the corresponding square.
and register the select.

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py - creating a select component
    :lines: 17-59
    :linenos:

First, we define our slot and colour options (*lines 1-31*),
then inside the button we set the placeholder text and options (*line 36-37*).

In the custom id we store the slot the user is currently working with (*line 39*),
whether they're picking a slot or a colour (*line 40*),
and we store the selected colours for the three slots (*lines 41-43*).

Next, we define the callback:

.. literalinclude:: ../../../examples/select.py
    :lines: 61-72
    :linenos:

.. tip::
    Since we're dealing with a select, :obj:`inter.values <disnake.MessageInteraction.values>` will never be ``None``.
    Therefore, the assertion will never raise.
    The assertion only serves to help the type checker realise this.

If the selection was a slot, run slot selection logic (*lines 5-6*).
To keep things tidy, we use a separate function for this.
Otherwise, run colour selection logic (*lines 8-9*).
Finally we render the new colours and update the select (*lines 77-78*).

Then we define ``handle_slots``:

.. literalinclude:: ../../../examples/select.py
    :lines: 74-84
    :linenos:

In case the user wishes to finalize, disable the select (*lines 2-5*).
Otherwise, we update options and display (*lines 7-8*)
and set the slot to the user's selection and set state to colour (*lines 10-11*).
The select will now enter colour selection mode.

Then we define ``handle_colours``:

.. literalinclude:: ../../../examples/select.py
    :lines: 86-90
    :linenos:

We update the options back to slot selection (*line 2*),
set the colour attribute for the current slot (*line 4*),
and set the state to slot (*line 5*).
The select will now re-enter slot selection mode.

Finally we define ``render_colours`` to simply render the three colour squares:

.. literalinclude:: ../../../examples/select.py
    :lines: 92-93


Source Code
-----------
:example:`select`

.. literalinclude:: ../../../examples/select.py
    :caption: examples/select.py
    :linenos:
