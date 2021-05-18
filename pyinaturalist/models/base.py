import attr
import json
from collections import UserList
from logging import getLogger
from os.path import expanduser
from pathlib import Path
from typing import IO, Dict, Generic, List, Type, TypeVar, Union

from pyinaturalist.response_format import try_datetime

# from naturtag.constants import JSON

aliased_kwarg = attr.ib(default=None, repr=False)
kwarg = attr.ib(default=None)
timestamp = attr.ib(converter=try_datetime, default=None)
logger = getLogger(__name__)


@attr.s
class BaseModel:
    """Base class for models"""

    id: int = kwarg
    partial: bool = kwarg

    @classmethod
    def from_json(cls, value: JSON, partial=False):
        """Create a new model object from a JSON path, file-like object, or API response object"""
        # Strip out Nones so we use our default factories instead (e.g. for empty lists)
        if not value:
            return cls()
        elif isinstance(value, dict):
            attr_names = attr.fields_dict(cls).keys()
            valid_json = {k: v for k, v in value.items() if k in attr_names and v is not None}
            return cls(**valid_json, partial=partial)  # type: ignore
        else:
            return _load_path_or_obj(value)  # type: ignore

    def to_json(self) -> Dict:
        return attr.asdict(self)


T = TypeVar('T', bound=BaseModel)


class ModelCollection(UserList, Generic[T]):
    """Base class representing a collection of model objects.
    This is used mainly for initializing from API responses, and some convenience methods that
    aggregate info from multiple objects.
    """

    data: List[T] = None
    model_cls: Type[BaseModel] = None

    @classmethod
    def model_class(cls) -> Type[BaseModel]:
        """Inspect the class to get the model type"""
        base = cls.__orig_bases__[0]  # e.g., ModelCollection[FooModel]
        return base.__args__[0]  # e.g. FooModel

    @classmethod
    def from_json(cls, value: JSON):
        """Initialize from a JSON path, file-like object, or API response"""
        if not value:
            return cls()
        elif isinstance(value, dict) and 'results' in value:
            value = value['results']
        if isinstance(value, list):
            return cls([cls.model_cls.from_json(item) for item in value])
        else:
            return cls(_load_path_or_obj(value))  # type: ignore

    def to_json(self) -> List[Dict]:
        return [item.to_json() for item in self.data]


def _load_path_or_obj(value: Union[IO, Path, str]):
    if isinstance(value, (Path, str)):
        with open(expanduser(str(value))) as f:
            return json.load(f)
    else:
        return json.load(value)
