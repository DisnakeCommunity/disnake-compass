"""Sphinx configuration."""

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import re
import subprocess
import sys

import disnake
import sphinx.config
from disnake.ext import commands


def git(*args: str) -> str:
    """Run a git command and return the output."""
    return subprocess.check_output(["git", *args], text=True).strip()


git_pwd = git("rev-parse", "--show-toplevel")
sys.path.append(os.path.abspath(git_pwd))

from docs.source import util

sys.modules["commands"] = commands
sys.path.append(os.path.abspath("./extensions"))

project = "disnake-compass"
copyright = "2023, Sharp-Eyes"  # noqa: A001
author = "Sharp-Eyes"
release = "1.0.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    # In sphinx.
    "sphinx.ext.autodoc",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.linkcode",
    "sphinx.ext.napoleon",
    # External.
    "sphinxcontrib_trio",
    "sphinxcontrib.towncrier.ext",
    "sphinx_inline_tabs",
    "sphinx_copybutton",
    "hoverxref.extension",
    "sphinx_autodoc_typehints",
    # Custom.
    "attributetable",
    "custom_documenter",
]
exclude_patterns = []

pygments_style = "friendly"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_theme_options = {
    "source_repository": "https://github.com/DisnakeCommunity/disnake-compass",
    "source_branch": "master",
    # Taken directly from Furo docs at https://github.com/pradyunsg/furo/blob/main/docs/conf.py.
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/DisnakeCommunity/disnake-compass/",
            "html": """
                    <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                        <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path>
                    </svg>
                """,  # noqa: E501
            "class": "",
        },
    ],
}
html_show_sourcelink = False

html_static_path = ["_static"]
html_css_files = [
    "./css/custom.css",
    "./css/attributetable.css",
    "./css/custom_documenter.css",
]
html_js_files = ["./js/custom.js"]

# -- Intersphinx config -------------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "disnake": ("https://docs.disnake.dev/en/stable/", None),
    "attrs": ("https://www.attrs.org/en/stable/", None),
}

# -- Autodoc config -----------------------------------------------------------

autodoc_member_order = "groupwise"
autodoc_typehints = "signature"
autodoc_typehints_format = "short"
autodoc_default_options = {"show-inheritance": True, "inherited-members": False}

# -- Hoverxref config ---------------------------------------------------------

hoverx_default_type = "tooltip"
hoverxref_domains = ["py"]
hoverxref_role_types = dict.fromkeys(
    ["ref", "class", "func", "meth", "attr", "exc", "data", "obj"],
    "tooltip",
)
hoverxref_tooltip_theme = ["tooltipster-custom"]
hoverxref_tooltip_lazy = True

# These have to match the keys on intersphinx_mapping, and those projects must
# be hosted on readthedocs.
hoverxref_intersphinx = list(intersphinx_mapping)


# -- Linkcode config ----------------------------------------------------------

repo_url = "https://github.com/DisnakeCommunity/disnake-compass"


def get_git_ref() -> str:
    """Return the current git reference."""
    # Current git reference. Uses branch/tag name if found, otherwise uses commit hash
    git_ref = git("name-rev", "--name-only", "--no-undefined", "HEAD")
    return re.sub(r"^(remotes/[^/]+|tags)/", "", git_ref)


git_ref = get_git_ref()
module_path = util.get_module_path()
linkcode_resolve = util.make_linkcode_resolver(module_path, repo_url, git_ref)


# -- Extlinks config ----------------------------------------------------------

extlinks = {
    "issue": (f"{repo_url}/issues/%s", "#%s"),
    "github": (f"{repo_url}/%s", "%s"),
    "github-blob": (f"{repo_url}/blob/{git_ref}/%s", "%s"),
    "example": (f"{repo_url}/blob/{git_ref}/examples/%s.py", "View on GitHub: %s.py"),
    "attrs": ("https://www.attrs.org/en/stable/%s", "%s"),
}

# -- towncrier config ---------------------------------------------------------

towncrier_draft_autoversion_mode = "draft"
towncrier_draft_include_empty = False  # hides the unreleased indicator if there are no changes
towncrier_draft_working_directory = git_pwd

# -- sphinx-autodoc-typehints config ------------------------------------------

# Apply monkeypatch.
util.apply_autodoc_typehints_patch()

typehints_document_rtype = False
typehints_use_rtype = False
simplify_optional_unions = True
always_use_bars_union = True
typehints_fully_qualified = False

# Customise display for specific types.
aliases: dict[object, str] = {
    # Idk why this is needed, but it is...
    disnake.ButtonStyle: ":class:`~disnake.ButtonStyle`",
}


def typehints_formatter(ann: object, _: sphinx.config.Config) -> str | None:
    """Format typehints."""
    if typehint := aliases.get(ann):
        return typehint

    return None
