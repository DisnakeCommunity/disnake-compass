# pyright: reportImportCycles = false
# pyright: reportWildcardImportFromLibrary = false
# ^ This is a false positive as it is confused with site-packages' disnake.

"""The main disnake-ext-components module.

An extension for disnake aimed at making component interactions with
listeners somewhat less cumbersome.
"""

from disnake.ext.components import api as api
from disnake.ext.components import internal as internal
from disnake.ext.components.fields import *
from disnake.ext.components.impl import *
