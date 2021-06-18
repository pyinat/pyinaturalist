from functools import update_wrapper
from inspect import signature
from typing import Any, Callable, Iterable, List

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
        if value and not _is_model_object_or_list(value):
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
        return make_attribute(self.temp_attr, init=True, repr=False, default=self.default)


def add_lazy_attrs(cls, fields):
    """A field transformer to do some post-processing on a model class while it's being created.
    For each :py:class:`.LazyProperty` on a model class, this adds a corresponding ``attr.field``
    in which to temporarily store a raw JSON value that will later be converted into a model object.
    """
    lazy_properties = [p for p in cls.__dict__.values() if isinstance(p, LazyProperty)]
    return list(fields) + [p.get_lazy_attr() for p in lazy_properties]


def get_model_fields(obj: Any) -> Iterable[Attribute]:
    """Add placeholder attributes for lazy-loaded model properties so they get picked up by rich's
    pretty-printer. Does not change behavior for anything except :py:class:`.BaseModel` subclasses.
    """
    from pyinaturalist.models import LazyProperty

    attrs = list(obj.__attrs_attrs__)
    if isinstance(obj, BaseModel):
        prop_names = [k for k, v in type(obj).__dict__.items() if isinstance(v, LazyProperty)]
        attrs += [make_attribute(p) for p in prop_names]
    return attrs


def make_attribute(name, **kwargs):
    kwargs = {**FIELD_DEFAULTS, **kwargs}
    return Attribute(name=name, **kwargs)


def _is_model_object_or_list(value):
    try:
        return isinstance(value, BaseModel) or isinstance(value[0], BaseModel)
    except (AttributeError, KeyError, TypeError):
        return False


def _returns_list(func: Callable) -> bool:
    """Determine if a function is annotated with a List return type"""
    return_type = signature(func).return_annotation
    return _get_origin(return_type) in (list, List)


def _get_origin(tp):
    """Get generic origin (for python 3.6 compatibility)"""
    if getattr(tp, '__origin__', None):
        return tp.__origin__
    if hasattr(tp, '_gorg') and hasattr(tp._gorg, '__mro__'):
        for t in tp._gorg.__mro__:
            if t.__module__ in ('builtins', '__builtin__') and t is not object:
                return t
    return tp
