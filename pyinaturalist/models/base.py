"""Base class and utilities for model objects. These do 3 main things:

1. Convert from response JSON to model objects
2. Enable lazy-loading of nested model objects for improved performance
3. Enable better pretty-printing output within Jupyter/REPL.

"""
import json
from datetime import datetime, timezone
from functools import update_wrapper
from inspect import signature
from logging import getLogger
from os.path import expanduser
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Type, TypeVar, Union

from attr import Attribute, Factory, asdict, define, field, fields_dict

from pyinaturalist.constants import AnyFile, ResponseOrFile
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


class LazyProperty(property):
    """A lazy-initialized/cached descriptor, similar to ``@functools.cached_property``, but works
    for slotted classes by not relying on ``__dict__``.

    Currently this is used to lazy-load nested model objects for better performance.
    How it works:

    1. Define a `LazyProperty` on a model, say ``MyModel.foo``
    2. Use `add_lazy_attrs` as a field_transformer for the model, which adds an attr.field ``_foo``
    3. During attrs init, ``_foo`` is set from response JSON
    4. When ``foo`` is first called, it converts ``_foo`` from JSON into a model object
    5. When ``foo`` is called again the previously converted ``_foo`` object will be returned

    Example::

        def converter_func(value) -> str:
            return str(value)

        def list_converter_func(value) -> List:
            return [value]

        @attrs.define(field_transformer=add_lazy_attrs)
        class MyModel(BaseModel):
            str_field = LazyProperty(converter_func)
            list_field = LazyProperty(list_converter_func)

            # Auto-generated fields will look like:
            # _str_field = field(factory=list)
            # _list_field = field(default=None)

    """

    def __init__(self, converter: Callable, name: str = None):
        self.converter = converter
        self.default = None
        self.__set_name__(None, name)
        update_wrapper(self, converter)

        # Use either a list factory or default value, depending on the converter's return type
        if _returns_list(converter):
            self.default = Factory(list)

    def __get__(self, obj, cls):
        """When accessing the value, convert it if it hasn't already been, and cache the converted
        value for subsequent calls.
        """
        if obj is None:
            return self

        value = getattr(obj, self.temp_attr)
        if value and not _is_model_object(value):
            value = self.converter(value)
            setattr(obj, self.temp_attr, value)
        return value

    def __set__(self, obj, raw_value):
        setattr(obj, self.temp_attr, raw_value)

    def __set_name__(self, owner, name):
        self.__name__ = name
        self.temp_attr = f'_{name}'

    def get_lazy_attr(self) -> Attribute:
        """Get an attribute corresponding to this LazyProperty instance"""
        return _get_attr(self.temp_attr, init=True, repr=False, default=self.default)


def add_lazy_attrs(cls, fields):
    """A field transformer to do some post-processing on a model class while it's being created.
    For each :py:class:`.LazyProperty` on a model class, this adds a corresponding ``attr.field``
    in which to temporarily store a raw JSON value that will later be converted into a model object.
    """
    lazy_properties = [p for p in cls.__dict__.values() if isinstance(p, LazyProperty)]
    return list(fields) + [p.get_lazy_attr() for p in lazy_properties]


# TODO: Do we want to print all properties, or just LazyProperties?
def get_model_fields(obj: Any) -> Iterable[Attribute]:
    """Add placeholder attributes for model @properties so they get picked up by rich's
    pretty-printer. Does not change behavior for anything except :py:class:`.BaseModel` subclasses.
    """
    attrs = list(obj.__attrs_attrs__)
    if isinstance(obj, BaseModel):
        prop_names = [k for k, v in type(obj).__dict__.items() if isinstance(v, property)]
        attrs += [_get_attr(p) for p in prop_names]
    return attrs


def load_json(value: AnyFile):
    """Load JSON from a file path or file-like object"""
    if isinstance(value, (Path, str)):
        with open(expanduser(str(value))) as f:
            return json.load(f)
    else:
        return json.load(value)


def _get_attr(name, **kwargs):
    kwargs = {**FIELD_DEFAULTS, **kwargs}
    return Attribute(name=name, **kwargs)


def _is_model_object(value):
    try:
        return isinstance(value, BaseModel) or isinstance(value[0], BaseModel)
    except (AttributeError, KeyError, TypeError):
        return False


def _returns_list(func: Callable) -> bool:
    """Determine if a function is annotated with a List return type"""
    return_type = signature(func).return_annotation
    return return_type.__origin__ is list
