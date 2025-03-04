Examples
========

.. _/disnake-compass: https://github.com/DisnakeCommunity/disnake-compass

Welcome to the examples section of our docs.
Basic understanding of python and the usage of disnake's components is considered pre-knowledge for these examples, along with some familiarity with :attrs:`attrs < >` classes or dataclasses.
If this is your first time using *disnake-compass*, we recommend looking at the :ref:`Quickstart Guide <quickstart>`.
The examples aim to show you how some of the features of this extension can be used and implemented.

These examples are also available on our :github-blob:`GitHub repository <>` without documentation, and are perfectly runnable as-is.
The easiest way of running the examples is:

1. Ensure `uv <https://docs.astral.sh/uv/>`_ is installed,
2. Clone the repository,
3. Copy ``.env.example`` and name it ``.env``,
4. Enter your bot token in the new ``.env`` file,
5. Run ``uv run task example <name>``.

If you think an example is unclear or an example for a feature is missing, feel free to open a :github:`pull request <pulls>` or :github:`issue <issues>`!

.. toctree::
    :maxdepth: 1
    :caption: Examples

    Attrs </examples/attrs>
    Button </examples/button>
    Manager </examples/manager>
    Select </examples/select>
