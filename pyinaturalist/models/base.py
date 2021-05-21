# TODO: Inherit from UserDict so model objects can also be used like dicts?
#   e.g. support both observation['id'] and observation.id
import json
from datetime import datetime, timezone
from functools import wraps
from logging import getLogger
from os.path import expanduser
from pathlib import Path
from typing import IO, Callable, Dict, List, Optional, Type, TypeVar, Union

from attr import asdict, define, field, fields_dict

from pyinaturalist.constants import JsonResponse
from pyinaturalist.response_format import convert_lat_long, try_datetime


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# Some aliases for common attribute types
kwarg = field(default=None)
coordinate_pair = field(converter=convert_lat_long, default=None)  # type: ignore
datetime_attr = field(converter=try_datetime, default=None)  # type: ignore
datetime_now_attr = field(converter=try_datetime, factory=utcnow)  # type: ignore


T = TypeVar('T', bound='BaseModel')
logger = getLogger(__name__)


@define(auto_attribs=False)
class BaseModel:
    """Base class for models"""

    partial: bool = kwarg
    temp_attrs: Optional[List] = None

    # Note: when used as converters, mypy will raise a false positive error. See:
    # https://github.com/python/mypy/issues/6172
    # https://github.com/python/mypy/issues/7912
    @classmethod
    def from_json(cls: Type[T], value: JsonResponse, partial=False):
        """Create a new model object from a JSON path, file-like object, or API response object.
        Omits invalid fields and ``None``s, so we use our default factories instead (e.g. for empty
        lists)
        """
        if not value:
            return cls()
        elif isinstance(value, dict):
            attr_names = [a.lstrip('_') for a in fields_dict(cls)]
            if cls.temp_attrs:
                attr_names.extend(cls.temp_attrs)
            valid_json = {k: v for k, v in value.items() if k in attr_names and v is not None}
            return cls(**valid_json, partial=partial)  # type: ignore
        else:
            return cls.from_json(_load_path_or_obj(value))  # type: ignore

    @classmethod
    def from_json_list(cls: Type[T], value: Union[IO, str, JsonResponse, List[JsonResponse]]) -> List:
        """Initialize from a JSON path, file-like object, or API response"""
        if not value:
            return []
        elif isinstance(value, dict) and 'results' in value:
            value = value['results']
        elif isinstance(value, dict):
            value = [value]  # type: ignore
        if isinstance(value, list):
            return [cls.from_json(item) for item in value]
        else:
            return cls.from_json_list(_load_path_or_obj(value))  # type: ignore

    def to_json(self) -> Dict:
        return asdict(self)


def cached_property(func: Callable) -> property:
    """Similar to ``@functools.cached_property``, but works for slotted classes. Caches return value
    of ``func```` to self._<name>_obj. Requires _<name>_obj to be defined for slotted classes.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        cached_attr = f'_{func.__name__}_obj'
        if not getattr(self, cached_attr):
            setattr(self, cached_attr, func(self, *args, **kwargs))
        return getattr(self, cached_attr)

    return property(wrapper)


def _load_path_or_obj(value: Union[IO, Path, str]):
    if isinstance(value, (Path, str)):
        with open(expanduser(str(value))) as f:
            return json.load(f)
    else:
        return json.load(value)
