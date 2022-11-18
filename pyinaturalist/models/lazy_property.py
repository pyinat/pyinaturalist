from functools import update_wrapper
from inspect import signature
from typing import Callable, Dict, List, Optional, Type

from attr import Attribute, Factory

from pyinaturalist.models import BaseModel

FIELD_DEFAULTS = {
    'default': None,
    'validator': None,
    'repr': True,
    'cmp': None,
    'hash': None,
    'init': False,
    'inherited': False,
}


class LazyProperty(property):
    """A lazy-initialized/cached descriptor for ``attrs`` classes. Its purpose is similar to
    ``@functools.cached_property``, but it works for slotted classes by not relying on ``__dict__``.

    Currently this is used to lazy-load nested model objects for better performance.

    How it's used:

    1. Define an ``attrs`` class
    2. Use ``add_lazy_attrs`` as a field_transformer for the class, which adds a temporary attributes
    3. Define a ``LazyProperty`` class attribute with a converter

    How it works:

    1. During attrs init, the temporary attribute is set containing a raw dict
    2. When ``foo`` is first accessed, it runs the converter on the temp attribute
    3. When ``foo`` is accessed again, the previously converted temp attribute will be returned

    Example::

        # Just pretend these are expensive conversion functions
        def converter_func(value) -> str:
            return str(value)

        def list_converter_func(value) -> List:
            return [value]

        @attrs.define(field_transformer=add_lazy_attrs)
        class MyModel(BaseModel):
            str_field = LazyProperty(converter_func)
            list_field = LazyProperty(list_converter_func)

            # Auto-generated temp attributes will look like:
            # _str_field = field(default=None)
            # _list_field = field(factory=list)

    """

    def __init__(
        self,
        converter: Callable,
        name: Optional[str] = None,
        doc: Optional[str] = None,
        type: Type = BaseModel,
        **converter_kwargs,
    ):
        update_wrapper(self, converter)
        self.converter = converter
        self.converter_kwargs = converter_kwargs
        self.default = None
        self.type = type
        self.__doc__ = doc
        self.__set_name__(None, name)

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
        if value and not _is_model_object_or_list(value):
            value = self.converter(value, **self.converter_kwargs)
            setattr(obj, self.temp_attr, value)

        return value

    def __set__(self, obj, raw_value):
        """When initially setting the value, store raw data in the temp attribute"""
        setattr(obj, self.temp_attr, raw_value)

    def __set_name__(self, owner, name):
        """Set the name of both the LazyProperty attribute and its temp attribute"""
        self.__name__ = name
        self.temp_attr = f'_{name}'

    def get_lazy_attr(self) -> Attribute:
        """Get a temp attribute to be used by this LazyProperty instance"""
        return make_attribute(self.temp_attr, init=True, repr=False, default=self.default)


def add_lazy_attrs(cls, fields):
    """A field transformer to do some post-processing on a model class while it's being created.
    For each :py:class:`.LazyProperty` on a model class, this adds a corresponding ``attr.field``
    in which to temporarily store a raw dict value that will later be converted into a model object.
    """
    lazy_properties = [p for p in cls.__dict__.values() if isinstance(p, LazyProperty)]
    return list(fields) + [p.get_lazy_attr() for p in lazy_properties]


def get_lazy_properties(cls: Type[BaseModel]) -> Dict[str, LazyProperty]:
    return {k: v for k, v in cls.__dict__.items() if isinstance(v, LazyProperty)}


def make_attribute(name, **kwargs):
    kwargs = {**FIELD_DEFAULTS, **kwargs}
    return Attribute(name=name, **kwargs)


# TODO: Make this more generic by looking for converter function return type instead of BaseModel?
def _is_model_object_or_list(value):
    try:
        return isinstance(value, BaseModel) or isinstance(value[0], BaseModel)
    except (AttributeError, KeyError, TypeError):
        return False


def _returns_list(func: Callable) -> bool:
    """Determine if a function is annotated with a List return type"""
    return_type = signature(func).return_annotation
    return getattr(return_type, '__origin__', None) in (list, List)
