"""Type-safe field selectors for the iNaturalist V2 API.

The V2 API accepts a ``fields`` parameter to control which response fields are returned.
This module provides typed, IDE-autocompletable selectors derived from the existing model classes.

Usage::

    from pyinaturalist.v2.fields import obs, fields_to_dict, apply_except_fields

    # Select specific fields
    get_observations(fields=[obs.taxon.name, obs.user.login])

    # Exclude specific (nested) fields
    get_observations(except_fields=[obs.identifications.taxon.ancestors])
"""

from __future__ import annotations

from copy import deepcopy

import attr

from pyinaturalist.models import BaseModel, Observation, Taxon
from pyinaturalist.models.lazy_property import get_lazy_properties

# Names of LazyProperties that are typed as BaseModel but are actually lists of Taxon
_TAXON_LIST_PROPS = {'ancestors', 'children'}


def _deep_merge(base: dict, addition: dict) -> dict:
    """Recursively merge ``addition`` into ``base`` (modifies ``base`` in place)."""
    for key, value in addition.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


class FieldPath:
    """A leaf field selector carrying its dot-notation path.

    Converts to the nested dict format the V2 API expects:
    ``FieldPath("taxon.name") -> {"taxon": {"name": True}}``
    """

    def __init__(self, path: str) -> None:
        self._path = path

    def to_dict(self) -> dict:
        """Convert this path to the nested dict the API expects."""
        parts = self._path.split('.')
        result: dict = True  # type: ignore[assignment]
        for part in reversed(parts):
            result = {part: result}
        return result

    def __repr__(self) -> str:
        return f'FieldPath({self._path!r})'

    def __str__(self) -> str:
        return self._path


class FieldSelector:
    """A subtree field selector built from an attrs model class.

    Each attribute on the model is exposed as either a :class:`FieldPath` (scalar field)
    or a nested :class:`FieldSelector` (LazyProperty referencing another model).

    Converts to the nested dict format the V2 API expects, including all child fields.
    Children carry their own full dot-notation paths, so ``to_dict()`` simply merges them.
    """

    _path: str
    _children: dict[str, FieldPath | FieldSelector]

    def __init__(self, path: str, _children: dict[str, FieldPath | FieldSelector]) -> None:
        # path is the full dot-notation path to this node (e.g. '' for root, 'identifications.taxon')
        object.__setattr__(self, '_path', path)
        object.__setattr__(self, '_children', _children)
        for attr_name, child in _children.items():
            object.__setattr__(self, attr_name, child)

    def to_dict(self) -> dict:
        """Convert this selector to a nested dict with all fields set to True.

        Children already carry full dot-notation paths, so this merges their dicts directly.
        """
        result: dict = {}
        for child in self._children.values():
            _deep_merge(result, child.to_dict())
        return result

    def __repr__(self) -> str:
        return f'FieldSelector({self._path!r})'

    def __str__(self) -> str:
        return self._path

    def __getattr__(self, name: str) -> FieldPath | FieldSelector:
        # Reached only for names not set during __init__; provides a typed return for mypy.
        raise AttributeError(f'{type(self).__name__!r} has no field {name!r}')

    def __setattr__(self, name: str, value: object) -> None:
        # All attributes (including private ones) are set only during construction via object.__setattr__
        raise AttributeError(f'FieldSelector attributes are read-only: {name!r}')


def _unwrap_list_type(tp: type) -> type:
    """Unwrap ``list[X]`` to ``X``; return ``tp`` unchanged for non-list types."""
    origin = getattr(tp, '__origin__', None)
    if origin is list:
        args = getattr(tp, '__args__', None)
        if args:
            return args[0]
    return tp


def _build_selector(
    model_cls: type[BaseModel],
    prefix: str = '',
    _visiting: set[type] | None = None,
) -> FieldSelector:
    """Build a :class:`FieldSelector` by introspecting an attrs model class.

    All :class:`FieldPath` leaves are built with their full dot-notation path (including prefix),
    so ``to_dict()`` on any selector or sub-selector produces the correct nested structure.

    Args:
        model_cls: The attrs model class to introspect.
        prefix: Dot-notation prefix for all paths in this subtree (e.g. ``'identifications.'``).
        _visiting: Set of model classes currently on the active recursion stack; used to detect
            cycles (e.g. Taxon → Taxon via ancestors/children).
    """
    if _visiting is None:
        _visiting = set()

    children: dict[str, FieldPath | FieldSelector] = {}

    # Add a FieldPath for each scalar attrs field (skip private and internal attrs)
    try:
        attrs_fields = attr.fields(model_cls)
    except attr.exceptions.NotAnAttrsClassError:
        attrs_fields = ()

    for f in attrs_fields:
        if f.name.startswith('_'):
            continue
        path = f'{prefix}{f.name}'
        children[f.name] = FieldPath(path)

    # Add nested FieldSelectors for each LazyProperty
    _visiting.add(model_cls)
    for prop_name, prop in get_lazy_properties(model_cls).items():
        if prop_name.startswith('_'):
            continue

        # Resolve the nested model class
        nested_cls: type[BaseModel]
        if prop_name in _TAXON_LIST_PROPS:
            # Taxon.ancestors/children are typed as BaseModel but are actually list[Taxon]
            nested_cls = Taxon
        else:
            nested_cls = _unwrap_list_type(prop.type)
            if not (isinstance(nested_cls, type) and issubclass(nested_cls, BaseModel)):
                # Can't introspect non-model types; fall back to a leaf FieldPath
                children[prop_name] = FieldPath(f'{prefix}{prop_name}')
                continue

        if nested_cls in _visiting:
            # Cycle detected — emit a leaf to avoid infinite recursion
            children[prop_name] = FieldPath(f'{prefix}{prop_name}')
            continue

        child_prefix = f'{prefix}{prop_name}.'
        children[prop_name] = _build_selector(nested_cls, child_prefix, _visiting)
    _visiting.discard(model_cls)

    # The selector's own path is the prefix without trailing dot (empty string for root)
    selector_path = prefix.rstrip('.')
    return FieldSelector(selector_path, children)


def fields_to_dict(
    fields: list | dict | str | None,
) -> dict | str | None:
    """Convert a list of :class:`FieldPath`/:class:`FieldSelector` objects to the nested dict the
    V2 API expects.

    Plain strings (e.g. ``'all'``) and plain dicts are passed through unchanged, preserving
    backward compatibility.

    Args:
        fields: One of:
            - ``list`` of :class:`FieldPath` / :class:`FieldSelector` objects
            - ``dict`` — passed through as-is
            - ``str`` (e.g. ``'all'``) — passed through as-is
            - ``None`` — returned as ``None``

    Returns:
        Merged nested dict, or the original value if it is not a list.
    """
    if fields is None or isinstance(fields, (str, dict)):
        return fields

    result: dict = {}
    for item in fields:
        if isinstance(item, (FieldPath, FieldSelector)):
            _deep_merge(result, item.to_dict())
        elif isinstance(item, dict):
            _deep_merge(result, item)
        elif isinstance(item, str):
            # Plain string field name — treat as a top-level True value
            result[item] = True
    return result


def apply_except_fields(
    base: dict,
    except_fields: list[FieldPath | FieldSelector | str],
) -> dict:
    """Deep-copy ``base`` and remove the paths specified by ``except_fields``.

    Supports nested dot-paths (e.g. ``obs.identifications.taxon.ancestors``) as well as plain
    strings for backward compatibility.

    Args:
        base: The full fields dict to start from (will not be modified).
        except_fields: Fields to exclude; may be :class:`FieldPath`, :class:`FieldSelector`,
            or plain strings.

    Returns:
        A copy of ``base`` with the specified fields removed.
    """
    result = deepcopy(base)

    for item in except_fields:
        if isinstance(item, str):
            path = item
        elif isinstance(item, (FieldPath, FieldSelector)):
            # Both FieldPath and FieldSelector expose their full dot-path via str()
            path = str(item)
        else:
            continue

        _remove_path(result, path.split('.'))

    return result


def _remove_path(d: dict, parts: list[str]) -> None:
    """Recursively remove a dot-path from a nested dict (in place)."""
    if not parts or not isinstance(d, dict):
        return
    key = parts[0]
    if key not in d:
        return
    if len(parts) == 1:
        del d[key]
    else:
        _remove_path(d[key], parts[1:])
        # Clean up empty intermediate dicts
        if isinstance(d[key], dict) and not d[key]:
            del d[key]


# ---------------------------------------------------------------------------
# Module-level selector instances
# ---------------------------------------------------------------------------

#: Field selector for :class:`~pyinaturalist.models.Observation`
obs: FieldSelector = _build_selector(Observation)

#: Field selector for :class:`~pyinaturalist.models.Taxon`
taxon: FieldSelector = _build_selector(Taxon)
