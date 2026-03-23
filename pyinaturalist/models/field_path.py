"""Typed field selection for the iNaturalist v2 API.

Allows users to select response fields using model class attributes instead of raw dicts or strings:

    get_observations(fields=[Observation.id, Observation.taxon.name, Observation.taxon.rank])
"""

from __future__ import annotations

from typing import Any


class FieldPath:
    """Represents a selected field path, e.g. ``FieldPath('taxon', 'name')`` -> ``'taxon.name'``.

    Used as the result of class-level attribute access on a model, e.g.::

        Observation.id           # FieldPath('id')
        Observation.taxon.name   # FieldPath('taxon', 'name')
    """

    def __init__(self, *parts: str):
        self.parts = parts

    def __repr__(self) -> str:
        return f'FieldPath({".".join(self.parts)!r})'

    def __eq__(self, other: object) -> bool:
        return isinstance(other, FieldPath) and self.parts == other.parts

    def __hash__(self) -> int:
        return hash(self.parts)


class FieldProxy:
    """Class-level proxy for a nested model. Attribute access yields :class:`FieldPath` objects
    for scalar fields or nested :class:`FieldProxy` objects for related models.

    Used internally when accessing a ``LazyProperty`` at class level, e.g.::

        Observation.taxon         # FieldProxy(Taxon, prefix=('taxon',))
        Observation.taxon.name    # FieldPath('taxon', 'name')
    """

    def __init__(self, model_cls: type, prefix: tuple[str, ...] = ()):
        # Use object.__setattr__ to avoid triggering __getattr__
        object.__setattr__(self, '_model_cls', model_cls)
        object.__setattr__(self, '_prefix', prefix)

    def __getattr__(self, name: str) -> FieldPath | FieldProxy:
        model_cls = object.__getattribute__(self, '_model_cls')
        prefix = object.__getattribute__(self, '_prefix')

        from pyinaturalist.models.lazy_property import LazyProperty

        # Check if the attribute is a LazyProperty on the model class
        for cls in model_cls.__mro__:
            if name in cls.__dict__:
                descriptor = cls.__dict__[name]
                if isinstance(descriptor, LazyProperty):
                    return FieldProxy(descriptor.type, prefix=prefix + (name,))
                break

        # Otherwise it's a scalar field
        return FieldPath(*prefix, name)

    def to_field_path(self) -> FieldPath:
        """Return a FieldPath representing this proxy itself (i.e. include the whole nested model)."""
        prefix = object.__getattribute__(self, '_prefix')
        return FieldPath(*prefix)

    def __repr__(self) -> str:
        model_cls = object.__getattribute__(self, '_model_cls')
        prefix = object.__getattribute__(self, '_prefix')
        return f'FieldProxy({model_cls.__name__!r}, prefix={prefix!r})'


class FieldDescriptor:
    """Descriptor that returns a :class:`FieldPath` at class level and delegates to the
    underlying slot/attr descriptor at instance level.

    Installed on each model class by :func:`~pyinaturalist.models._install_field_descriptors_on`
    after all model classes have been fully built by attrs.
    """

    def __init__(self, field_name: str, slot_descriptor: Any):
        self._field_path = FieldPath(field_name)
        self._slot = slot_descriptor

    def __get__(self, obj: Any, cls: type) -> Any:
        if obj is None:
            return self._field_path
        return self._slot.__get__(obj, cls)

    def __set__(self, obj: Any, value: Any) -> None:
        self._slot.__set__(obj, value)


def build_fields_dict(fields: list) -> dict:
    """Convert a list of :class:`FieldPath` / :class:`FieldProxy` objects into the nested dict
    structure the v2 API expects.

    Examples::

        build_fields_dict([FieldPath('id')])
        # -> {'id': True}

        build_fields_dict([FieldPath('taxon', 'name'), FieldPath('taxon', 'rank')])
        # -> {'taxon': {'name': True, 'rank': True}}

        build_fields_dict([FieldProxy(Taxon, prefix=('taxon',))])
        # -> {'taxon': True}
    """
    result: dict = {}
    for item in fields:
        if isinstance(item, FieldProxy):
            item = item.to_field_path()
        if not isinstance(item, FieldPath):
            continue
        _merge_path(result, item.parts)
    return result


def _merge_path(d: dict, parts: tuple[str, ...]) -> None:
    """Recursively merge a field path into a nested dict."""
    if not parts:
        return
    key = parts[0]
    if len(parts) == 1:
        # If there's already a dict here (from a prior nested field), keep it
        if not isinstance(d.get(key), dict):
            d[key] = True
    else:
        if not isinstance(d.get(key), dict):
            d[key] = {}
        _merge_path(d[key], parts[1:])


def contains_field_paths(fields: Any) -> bool:
    """Return True if ``fields`` is a list containing any :class:`FieldPath` or
    :class:`FieldProxy` objects.
    """
    return isinstance(fields, list) and any(isinstance(f, (FieldPath, FieldProxy)) for f in fields)
