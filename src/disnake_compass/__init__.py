# pyright: reportImportCycles = false
# pyright: reportWildcardImportFromLibrary = false
# ^ This is a false positive as it is confused with site-packages' disnake.

"""The main disnake-compass module.

An extension for disnake aimed at making component interactions with
listeners somewhat less cumbersome.
"""

from disnake_compass import api as api
from disnake_compass import internal as internal
from disnake_compass.fields import *
from disnake_compass.impl import *
