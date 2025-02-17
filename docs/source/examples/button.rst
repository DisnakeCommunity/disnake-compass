Button
======

Step-by-Step
------------

A simple example on the use of buttons with disnake-compass.
This component is a button that increments its label each time it is clicked.

.. literalinclude:: ../../../examples/button.py
    :caption: examples/button.py - create a component
    :lines: 16-25
    :emphasize-lines: 2, 4

This button comes with its ``label = "0"``, and an integer variable ``count = 0`` that is stored in the custom id.
In the callback -- which is ran every time the button is clicked -- we increment the count and update the label to match the count.
We then edit the message with the updated button.

Finally, we make a command that sends the component.
Since ``count`` has a default, we do not need to specify it when instantiating the component.

.. literalinclude:: ../../../examples/button.py
    :caption: examples/button.py - create a command and send the component
    :lines: 28-33

Source code
-----------
:example:`button`

.. literalinclude:: ../../../examples/button.py
    :caption: examples/button.py
    :linenos:
