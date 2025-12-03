.. currentmodule:: disnake_compass

.. _whats_new:

Changelog
=========

This page keeps a detailed human friendly rendering of what's new and changed
in specific versions. Please see :ref:`version_guarantees` for more information.

.. towncrier-draft-entries:: |release| [UNRELEASED]

.. towncrier release notes start

.. _vp1p1p0:

v1.1.0
------

Breaking Changes
~~~~~~~~~~~~~~~~
- Remove the ``RichComponent.factory`` class variable and replace it with new :meth:`.RichComponent.get_factory` and :meth:`.RichComponent.set_factory` class methods. (:issue:`39`)
- Remove the ``RichComponent.manager`` class variable and replace it with new :meth:`.RichComponent.get_manager` and :meth:`.RichComponent.set_manager` instance methods. (:issue:`39`)
- :meth:`ComponentManager.register_component` and :meth:`ComponentManager.deregister_component` have been modified, and certain internal behaviour has changed. (:issue:`48`)
    More noticeably, :meth:`ComponentManager.deregister_component` now takes a component identifier rather than a full class.
- :meth:`RichComponent.get_manager` and :meth:`RichComponent.set_manager` are now class methods. (:issue:`48`)
- Modify :meth:`ComponentManager.parse_message_components` to take components directly and return a sequence of disnake UI components to support parsing v2 components. (:issue:`50`)
- Remove ``ComponentManager.finalise_components`` in favour of :meth:`ComponentManager.update_layout`. (:issue:`50`)

Deprecations
~~~~~~~~~~~~
- Deprecate ``ComponentManager.parse_message_interaction`` in favour of :meth:`.ComponentManager.parse_raw_component`. (:issue:`39`)

New Features
~~~~~~~~~~~~
- Add a new :obj:`~.FieldType.META` :class:`.FieldType` for component fields that should *not* be stored in the custom ID (:obj:`.FieldType.CUSTOM_ID`) and should *not* be inferred from the raw disnake component (:obj:`.FieldType.INTERNAL`). (:issue:`39`)
- Make the :class:`.RichComponent` :class:`~typing.Protocol` runtime-checkable. (:issue:`39`)
- Support :obj:`~.ComponentManager.register`\ing the same component to multiple :class:`.ComponentManager`\s. (:issue:`39`)
- The :class:`ComponentManager` instance is now immediately stored on a :class:`RichComponent` when it is registered. (:issue:`48`)
    This should reduce the number of times you need to manually provide a manager to :meth:`RichComponent.as_ui_component` etc.
- Add :meth:`ComponentManager.update_layout` to update a disnake UI component layout in-place with rich components (v1 and v2 compatible). (:issue:`50`)

.. _vp1p0p1:

v1.0.1
------

Documentation
~~~~~~~~~~~~~
- Introduce towncrier for changelogs. (:issue:`41`)
- Fix source code links and installation instructions and some miscellaneous issues. (:issue:`42`)
