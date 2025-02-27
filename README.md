NOTE
====

This branch is currently in alpha state. As of right now, buttons and selects are supported, and modals are yet to be implemented. Help with development would be very much appreciated. If you're interested in helping, please keep an eye on the repo's issues and [the TODO-section of this readme](https://github.com/DisnakeCommunity/disnake-compass/tree/docs#to-do).

disnake-compass
======================

An extension for [disnake](https://github.com/DisnakeDev/disnake) aimed at making component interactions with listeners somewhat less cumbersome.  
Requires disnake version 2.5.0 or above and python 3.8.0 or above.

Key Features
------------
- Smoothly integrates with disnake,
- Uses an intuitive dataclass-like syntax to create stateless persistent components,
- `custom_id` matching, conversion, and creation are automated for you,

Installing
----------

**Python 3.8 or higher and disnake 2.5.0 or higher are required**

To install the extension, run the following command in your command prompt/shell:

``` sh
# Linux/macOS
python3 -m pip install -U git+https://github.com/DisnakeCommunity/disnake-compass.git@docs

# Windows
py -3 -m pip install -U git+https://github.com/DisnakeCommunity/disnake-compass@docs
```
It will be installed to your existing [disnake](https://github.com/DisnakeDev/disnake) installation as an extension. From there, it can be imported as:

```py
from disnake.ext import components
```

Examples
--------
A very simple component that increments its label each time you click it can be written as follows:

```py
import disnake
from disnake.ext import commands
import disnake_compass


bot = commands.InteractionBot()
manager = disnake_compass.get_manager()
manager.add_to_bot(bot)


@manager.register
class MyButton(disnake_compass.RichButton):
    count: int

    async def callback(self, interaction: disnake.MessageInteraction) -> None:
        self.count += 1
        self.label = str(self.count)

        await interaction.response.edit_message(components=self)


@bot.slash_command()
async def test_button(interaction: disnake.CommandInteraction) -> None:
    component = await MyButton(label="0", count=0).as_ui_component()

    await interaction.send(components=component)


bot.run("TOKEN")
```

For extra examples, please see [the examples folder](https://github.com/DisnakeCommunity/disnake-compass/tree/docs/examples).

To-Do
-----
- Implement modals,
- Improve Cog support by somehow injecting the cog instance,
- PyPI release,
- Contribution guidelines,

Contributing
------------
Any contributions are welcome, feel free to open an issue or submit a pull request if you would like to see something added. Contribution guidelines will come soon.
