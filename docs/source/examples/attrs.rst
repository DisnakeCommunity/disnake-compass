Attrs
=====

Step-by-Step
------------

An example showcasing how :attrs:`attrs <>` utilities can be used with disnake-compass.

Say we wish to create a component, but we do not know the number of options beforehand, and we would like the user to be able to select all of them. It can be cumbersome to manually keep updating the ``max_values`` parameter of the select.

.. literalinclude:: ../../../examples/attrs.py
    :caption: examples/attrs.py - create a select
    :lines: 15, 19-28

To create an instance of this select where all options are selectable, we would need to do the following:

.. code-block:: python

    options = [...]
    select = CustomisableSelect(options=options, max_values=len(options))

Luckily, with the knowledge that *disnake-compass* is built upon :attrs:`attrs <>`, a few options become available to us.

For this example, we will be making use of attrs classes' :attrs:`__attrs_post_init__ <init.html#post-init/>` method, which is called immediately after attrs finishes its normal initialisation logic. If you're more familiar with dataclasses, this is essentially the same as dataclasses' similarly named ``__post_init__`` method.

.. literalinclude:: ../../../examples/attrs.py
    :caption: examples/attrs.py - create a select
    :lines: 15-28
    :emphasize-lines: 2-3

This allows the select to be created as follows:

.. code-block:: python

    options = [...]
    select = CustomisableSelect(options=options)

Then we create our test command and send the previously created customisable select.

.. literalinclude:: ../../../examples/attrs.py
    :caption: examples/attrs.py - create a command
    :lines: 31-49
    :linenos:

If the string is empty or whitespace, the user did not provide options (*lines 3-5*).
Next, we make the options by splitting over commas (*lines 7-10*).
Before creating the component, validate that there's max 25 options (*lines 12-14*).
Finally, if everything went correctly, we send the component (*lines 16-19*).


Source Code
-----------
:example:`attrs`

.. literalinclude:: ../../../examples/attrs.py
    :caption: examples/attrs.py
    :linenos:
