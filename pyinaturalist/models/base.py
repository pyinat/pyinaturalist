"""Base class and utilities for data models"""
import json
from collections import UserList
from logging import getLogger
from os.path import expanduser
from pathlib import Path
from typing import Dict, Generic, List, Type, TypeVar

from attr import asdict, define, field, fields_dict

from pyinaturalist.constants import AnyFile, JsonResponse, ResponseOrFile, ResponseOrResults, TableRow
from pyinaturalist.converters import ensure_list

T = TypeVar('T', bound='BaseModel')
TC = TypeVar('TC', bound='BaseModelCollection')
logger = getLogger(__name__)


@define(auto_attribs=False)
class BaseModel:
    """Base class for data models"""

    id: int = field(default=None, metadata={'doc': 'Unique record ID'})
    temp_attrs: List[str] = []
    headers: Dict[str, str] = {}

    @classmethod
    def from_json(cls: Type[T], value: JsonResponse, **kwargs) -> T:
        """Initialize a single model object from an API response or response result.
        Omits any invalid fields and ``None`` values, so we use our default factories instead
        (e.g. for empty dicts and lists).
        """
        if isinstance(value, cls):
            return value

        attr_names = [a.lstrip('_') for a in fields_dict(cls)]
        if cls.temp_attrs:
            attr_names.extend(cls.temp_attrs)

        valid_json = {k: v for k, v in value.items() if k in attr_names and v is not None}
        return cls(**valid_json, **kwargs)

    @classmethod
    def from_json_file(cls: Type[T], value: AnyFile) -> List[T]:
        """Initialize a collection of model objects from a JSON string, file path, or file-like object"""
        return cls.from_json_list(load_json(value))

    @classmethod
    def from_json_list(cls: Type[T], value: ResponseOrResults) -> List[T]:
        """Initialize a collection of model objects from an API response or response results"""
        return [cls.from_json(item) for item in ensure_list(value)]

    @property
    def row(self) -> TableRow:
        """Get values and headers to display as a row in a table"""
        raise NotImplementedError

    # TODO: Use cattr.unstructure() to handle recursion properly (for nested model objects)?
    def to_json(self) -> Dict:
        return asdict(self)


# TODO: Better workaround for mypy not accepting subclasses in overridden attributes and methods
@define(auto_attribs=False, order=False, slots=False)
class BaseModelCollection(BaseModel, UserList, Generic[T]):
    """Base class for data model collections. These will behave the same as lists but enable some
    additional operations on contained items.
    """

    data: List[T] = field(factory=list, init=False, repr=False)
    _id_map: Dict[int, T] = field(default=None, init=False, repr=False)

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
