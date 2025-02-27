NOTE
====

disnake-compass
===============

An extension for [disnake](https://github.com/DisnakeDev/disnake) aimed at making component interactions with listeners somewhat less cumbersome.  
Requires disnake version 2.10.0 or above and python 3.10.0 or above.

Key Features
------------
- Smoothly integrates with disnake,
- Uses an intuitive dataclass-like syntax to create innately persistent components,
- `custom_id` matching, conversion, and creation are automated for you.

Installing
----------

**Python 3.10 or higher and disnake 2.10.0 or higher are required**

To install the extension, run the following command in your command prompt/shell:

``` sh
# Linux/macOS
python3 -m pip install -U disnake-compass

# Windows
py -3 -m pip install -U disnake-compass
```
It can then be imported as
```py
import disnake_compass
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
manager.add_to_client(bot)


@manager.register
class MyButton(disnake_compass.RichButton):
    count: int

    async def callback(self, interaction: disnake.MessageInteraction[disnake.Client]) -> None:
        self.count += 1
        self.label = str(self.count)

        await interaction.response.edit_message(components=self)


@bot.slash_command()
async def test_button(interaction: disnake.CommandInteraction[disnake.Client]) -> None:
    component = await MyButton(label="0", count=0).as_ui_component()

    await interaction.send(components=component)


bot.run("TOKEN")
```

For extra examples, please see [the examples folder](https://github.com/DisnakeCommunity/disnake-compass/tree/docs/examples).

To-Do
-----
- Implement modals,
- Improve Cog support by somehow injecting the cog instance,
- Contribution guidelines,

Contributing
------------
Any contributions are welcome, feel free to open an issue or submit a pull request if you would like to see something added. Contribution guidelines will come soon.
