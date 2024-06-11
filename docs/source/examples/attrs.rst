Attrs
=====

An example showcasing how attrs utilities can be used with ext-components.

Say we wish to create a component, but we do not know the number of options beforehand, and we would like the user to be able to select all of them. It can be cumbersome to manually keep updating the ``max_values`` parameter of the select.

Luckily, with the knowledge that ext-components is built upon the ``attrs`` lib, a few options become available to us.


For this example, we will be making use of attrs classes' `__attrs_post_init__ <https://www.attrs.org/en/stable/init.html#post-init/>`_ method, which is called immediately after attrs finishes its normal initialisation logic. If you're familiar with dataclasses, this is essentially the same as a dataclass' ``__post_init__`` method.

First and foremost, we create a bot as per usual. Since we don't need any prefix command capabilities, we opt for an :class:`~disnake.ext.commands.InteractionBot`.

.. literalinclude:: ../../../examples/attrs.py
    :caption: examples/attrs.py - create a Bot object
    :lines: 3-8

Next, we make a component manager and register it to the bot.

.. literalinclude:: ../../../examples/attrs.py
    :caption: examples/attrs.py - create a manager and registering it
    :lines: 10-11

Now we create our customizable select.

.. literalinclude:: ../../../examples/attrs.py
    :caption: examples/attrs.py - create a select
    :lines: 14-28
    :emphasize-lines: 1, 3-4

Now, we ensure that max_values adapts to the passed number of options.
Since rich components use attrs under the hood, this can easily be
achieved through the ``__attrs_post_init__`` method.

.. literalinclude:: ../../../examples/attrs.py
    :caption: examples/attrs.py - customisation logic
    :lines: 16-17

Then we create our test command and send the previously created customisable select.

.. literalinclude:: ../../../examples/attrs.py
    :caption: examples/attrs.py - create a command
    :lines: 31-56
    :linenos:

If the string is empty or whitespace, the user did not provide options (*lines 10-12*).
Next, we make the options by splitting over commas (*lines 14-17*).
Before creating the component, validate that there's max 25 options (*lines 19-21*).
Finally if everything went correctly, we send the component.

Lastly, we run the bot.

.. literalinclude:: ../../../examples/attrs.py
    :caption: examples/attrs.py - run the bot
    :lines: 59

Source Code
-----------

.. literalinclude:: ../../../examples/attrs.py
    :caption: examples/attrs.py
    :lines: 3-59
    :emphasize-lines: 8-9, 12, 14-15, 57
    :linenos:
