"""Base class and utilities for data models"""
import json
from collections import UserList
from copy import deepcopy
from datetime import datetime
from logging import getLogger
from os.path import expanduser
from pathlib import Path
from typing import Dict, Generic, List, Type, TypeVar

from attr import Factory, asdict, define, field, fields, fields_dict

from pyinaturalist.constants import (
    DATETIME_SHORT_FORMAT,
    AnyFile,
    JsonResponse,
    ResponseOrFile,
    ResponseOrResults,
    TableRow,
)
from pyinaturalist.converters import ensure_list

T = TypeVar('T', bound='BaseModel')
TC = TypeVar('TC', bound='BaseModelCollection')
logger = getLogger(__name__)


@define(auto_attribs=False)
class BaseModel:
    """Base class for data models"""

    id: int = field(default=None, metadata={'doc': 'Unique record ID'})
    _nested: bool = field(default=False, repr=False, init=False)
    temp_attrs: List[str] = []

    @classmethod
    def copy(cls, obj: 'BaseModel') -> 'BaseModel':
        """Copy a model object. This is defined as a classmethod to easily initialize a subclass
        from a parent class instance. For copying an instance to the same type,
        :py:func:`copy.deepcopy` can be used.
        """
        kwargs = obj.to_dict(recurse=False)
        return cls(**kwargs)

    @classmethod
    def from_json(cls: Type[T], value: JsonResponse, **kwargs) -> T:
        """Initialize a single model object from an API response or response result.

        Omits any invalid fields and ``None`` values, so default factories are used instead
        (e.g. for empty dicts and lists).
        """
        value = value or {}
        if isinstance(value, cls):
            return value

        cls_attrs = {k.lstrip('_'): v for k, v in fields_dict(cls).items()}

        def is_valid_attr(k):
            return (k in cls_attrs and cls_attrs[k].init is True) or k in cls.temp_attrs

        valid_json = {k: v for k, v in value.items() if is_valid_attr(k) and v is not None}
        return cls(**valid_json, **kwargs)

    @classmethod
    def from_json_file(cls: Type[T], value: AnyFile) -> List[T]:
        """Initialize a collection of model objects from a JSON string, file path, or file-like object"""
        return cls.from_json_list(load_json(value))

    @classmethod
    def from_json_list(cls: Type[T], value: ResponseOrResults, **kwargs) -> List[T]:
        """Initialize a collection of model objects from an API response or response results"""
        return [cls.from_json(item, **kwargs) for item in ensure_list(value)]

    @property
    def _row(self) -> TableRow:
        """Get values and headers to display as a row in a table"""
        raise NotImplementedError

    @property
    def _str_attrs(self) -> List[str]:
        """Get the subset of attribute names to show in the model's string representation"""
        raise NotImplementedError

    def to_dict(self, **kwargs) -> JsonResponse:
        """Convert this object back to dict format"""

        def vs(_inst, _key, value):
            return value.to_dict() if isinstance(value, BaseModel) else value

        obj_dict = asdict(self, value_serializer=vs, retain_collection_types=True, **kwargs)
        for a in fields(self.__class__):
            if a.init is False:
                obj_dict.pop(a.name, None)

        return {k.lstrip('_'): v for k, v in obj_dict.items()}

    def __rich_repr__(self):
        """Custom output to use when pretty-printed with rich. Compared to default rich behavior for
        attrs classes, this does the following:

        * Inform rich about all default values, including factories, so they will be excluded from
          output
        * Stringify datetime objects
        * Add lazy-loaded attributes to the output
        * Use condensed (str) representations of lazy-loaded attributes
        * Does not currently handle positional-only args (since we don't currently have any)

        This makes output much more readable, particularly within Jupyter or a REPL. Otherwise, some
        objects (especially observations) can turn into a huge wall of text several pages long.
        """
        from pyinaturalist.models import get_lazy_properties

        # If this is a nested object, show only a minimal representation
        if self._nested:
            for a in self._str_attrs:
                value = getattr(self, a)
                if isinstance(value, datetime):
                    value = value.strftime(DATETIME_SHORT_FORMAT)
                yield a, value, None
            return

        # Handle regular public attributes
        public_attrs = [
            a for a in self.__attrs_attrs__ if a.repr is True and not a.name.startswith('_')
        ]
        for a in public_attrs:
            default = a.default.factory() if isinstance(a.default, Factory) else a.default
            value = getattr(self, a.name)
            value = str(value) if isinstance(value, datetime) else value
            yield a.name, value, default

        # Handle LazyProperties
        for name, prop in get_lazy_properties(type(self)).items():
            yield name, prop.__get__(self, type(self))

    def __str__(self):
        """Make a string representation based on a minimal set of attributes defined on each model,
        via ``_str_attrs``.
        """
        repr_attrs = {a: getattr(self, a) for a in self._str_attrs}
        for k, v in repr_attrs.items():
            if isinstance(v, datetime):
                repr_attrs[k] = v.strftime(DATETIME_SHORT_FORMAT)
        repr_attrs_str = ', '.join([f'{k}={v}' for k, v in repr_attrs.items()])
        return f'{self.__class__.__name__}({repr_attrs_str})'


@define(auto_attribs=False, order=False, slots=False)
class BaseModelCollection(BaseModel, UserList, Generic[T]):
    """Base class for data model collections. These will behave the same as lists but enable some
    additional operations on contained items.
    """

    data: List[T] = field(factory=list, init=False, repr=False)
    _id_map: Dict[int, T] = field(default=None, init=False, repr=False)

    @classmethod
    def copy(cls, obj):
        """Copy a model collection"""
        return cls(data=[deepcopy(item) for item in obj])

    @classmethod
    def from_json(cls: Type[TC], value: JsonResponse, **kwargs) -> TC:
        if 'results' in value:
            value = value['results']
        if 'data' not in value:
            value = {'data': value}
        return super(BaseModelCollection, cls).from_json(value)

    @classmethod
    def from_json_list(cls: Type[TC], value: JsonResponse, **kwargs) -> TC:  # type: ignore
        """For model collections, initializing from a list should return an instance of ``cls``
        instead of a builtin ``list``
        """
        return cls.from_json(value)

    @property
    def id_map(self) -> Dict[int, T]:
        """A mapping of objects by unique identifier"""
        if self._id_map is None:
            self._id_map = {obj.id: obj for obj in self.data}
        return self._id_map

    def deduplicate(self):
        """Remove any duplicates from this collection based on ID"""
        self.data = list(self.id_map.values())

    def get_count(self, id: int, count_field: str = 'count') -> int:
        """Get a count associated with the given ID.
        Returns 0 if the collection type is not countable or the ID doesn't exist.
        """
        return getattr(self.id_map.get(id), count_field, 0)

    def __str__(self) -> str:
        return '\n'.join([str(obj) for obj in self.data])


def load_json(value: ResponseOrFile) -> ResponseOrResults:
    """Load a JSON string, file path, or file-like object"""
    if not value:
        return {}
    if isinstance(value, (dict, list)):
        json_value = value
    elif isinstance(value, (Path, str)):
        with open(expanduser(str(value))) as f:
            json_value = json.load(f)
    else:
        json_value = json.load(value)  # type: ignore

    if 'results' in json_value:
        json_value = json_value['results']
    return json_value
