# pyright: reportImportCycles = false
# pyright: reportWildcardImportFromLibrary = false
# ^ This is a false positive as it is confused with site-packages' disnake.

"""The main disnake-compass module.

An extension for disnake aimed at making component interactions with
listeners somewhat less cumbersome.
"""

__title__ = "disnake-compass"
__author__ = "Sharp-Eyes"
__license__ = "MIT"
__copyright__ = "Copyright 2023-present Sharp-Eyes"
__version__ = "1.0.0"

from disnake import VersionInfo as _VersionInfo

from disnake_compass import api as api
from disnake_compass import internal as internal
from disnake_compass.fields import *
from disnake_compass.impl import *

version_info = _VersionInfo(major=1, minor=0, micro=0, releaselevel="final", serial=0)

del _VersionInfo
