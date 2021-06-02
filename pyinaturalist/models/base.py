"""Base class and utilities for model objects"""
import json
from datetime import datetime, timezone
from logging import getLogger
from os.path import expanduser
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Type, TypeVar, Union

from attr import Attribute, asdict, define, field, fields_dict

from pyinaturalist.constants import AnyFile, JsonResponse, ResponseOrFile
from pyinaturalist.response_format import convert_lat_long, try_datetime

FIELD_DEFAULTS = {
    'default': None,
    'validator': None,
    'repr': True,
    'cmp': None,
    'hash': None,
    'init': False,
    'inherited': False,
}
T = TypeVar('T', bound='BaseModel')
logger = getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# Some aliases for common attribute types
kwarg = field(default=None)
coordinate_pair = field(converter=convert_lat_long, default=None)  # type: ignore
datetime_attr = field(converter=try_datetime, default=None)  # type: ignore
datetime_now_attr = field(converter=try_datetime, factory=utcnow)  # type: ignore


@define(auto_attribs=False)
class BaseModel:
    """Base class for models"""

    partial: bool = field(default=None, repr=False)
    temp_attrs: Optional[List] = None

    # Note: when using classmethods as converters, mypy will raise a false positive error, hence all
    # the `type: ignore` statements. See:
    # https://github.com/python/mypy/issues/6172
    # https://github.com/python/mypy/issues/7912
    @classmethod
    def from_json(cls: Type[T], value: ResponseOrFile, partial=False) -> Optional['BaseModel']:
        """Create a single model object from a JSON path, file-like object, or API response object.
        If multiple objects are present in JSON, only the first will be used.
        Omits invalid fields and ``None``, so we use our default factories instead (e.g. for empty
        lists).
        """
        if value is None or isinstance(value, BaseModel):
            return value
        json_value = value if isinstance(value, dict) else load_json(value)
        if 'results' in json_value:
            json_value = json_value['results'][0]

        attr_names = [a.lstrip('_') for a in fields_dict(cls)]
        if cls.temp_attrs:
            attr_names.extend(cls.temp_attrs)
        valid_json = {k: v for k, v in json_value.items() if k in attr_names and v is not None}
        return cls(**valid_json, partial=partial)  # type: ignore

    @classmethod
    def from_json_list(
        cls: Type[T], value: Union[ResponseOrFile, List[ResponseOrFile]]
    ) -> List['BaseModel']:
        """Initialize from a JSON path, file-like object, or API response"""
        if not value:
            return []
        elif isinstance(value, dict) and 'results' in value:
            value = value['results']
        elif isinstance(value, dict):
            value = [value]  # type: ignore

        if isinstance(value, list):
            obj_list = [cls.from_json(item) for item in value]
            return [obj for obj in obj_list if obj]
        else:
            return cls.from_json_list(load_json(value))  # type: ignore

    def to_json(self) -> Dict:
        return asdict(self)


# TODO: Do we want to print all properties, or just LazyProperties?
def get_model_fields(obj: Any) -> Iterable[Attribute]:
    """Add placeholder attributes for model @properties so they get picked up by rich's
    pretty-printer. Does not change behavior for anything except :py:class:`.BaseModel` subclasses.
    """
    attrs = list(obj.__attrs_attrs__)
    if isinstance(obj, BaseModel):
        prop_names = [k for k, v in type(obj).__dict__.items() if isinstance(v, property)]
        attrs += [make_attribute(p) for p in prop_names]
    return attrs


def load_json(value: Union[JsonResponse, AnyFile]):
    """Load JSON from a file path or file-like object"""
    if isinstance(value, dict):
        return value
    if isinstance(value, (Path, str)):
        with open(expanduser(str(value))) as f:
            return json.load(f)
    else:
        return json.load(value)


def make_attribute(name, **kwargs):
    kwargs = {**FIELD_DEFAULTS, **kwargs}
    return Attribute(name=name, **kwargs)
