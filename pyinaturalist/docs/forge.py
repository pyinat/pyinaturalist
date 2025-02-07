# ruff: noqa: C901
"""Vendored copy of python-forge, used due to inactive maintenance and installation issues with
PyPI wheel.

Source repo: https://github.com/dfee/forge
Author: Devin Fee
License:

The MIT License (MIT)

Copyright (c) 2018 Devin Fee

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import asyncio
import builtins
import collections
import functools
import inspect
import types
import typing

# Convenience
_TYPE_FP_CTX_CALLABLE = typing.Callable[
    [typing.Any, str, typing.Any],
    typing.Any,
]
_TYPE_FP_KIND = inspect._ParameterKind  # pylint: disable=C0103, invalid-name
_TYPE_FP_BOUND = bool  # pylint: disable=C0103, invalid-name
_TYPE_FP_CONTEXTUAL = bool  # pylint: disable=C0103, invalid-name
_TYPE_FP_NAME = typing.Optional[str]
_TYPE_FP_DEFAULT = typing.Any
_TYPE_FP_FACTORY = typing.Callable[[], typing.Any]
_TYPE_FP_TYPE = typing.Any
_TYPE_FP_CONVERTER = typing.Optional[
    typing.Union[_TYPE_FP_CTX_CALLABLE, typing.Iterable[_TYPE_FP_CTX_CALLABLE]]
]
_TYPE_FP_VALIDATOR = typing.Optional[
    typing.Union[_TYPE_FP_CTX_CALLABLE, typing.Iterable[_TYPE_FP_CTX_CALLABLE]]
]
_TYPE_FP_METADATA = typing.Mapping

_run_validators = True


def get_run_validators() -> bool:
    """
    Check whether validators are enabled.
    :returns: whether or not validators are run.
    """
    return _run_validators


def set_run_validators(run: bool) -> None:
    """
    Set whether or not validators are enabled.
    :param run: whether the validators are run
    """
    # pylint: disable=W0603, global-statement
    if not isinstance(run, bool):
        raise TypeError("'run' must be bool.")
    global _run_validators
    _run_validators = run


class Counter:
    """
    A counter whose instances provides an incremental value when called

    :ivar count: the next index for creation.
    """

    __slots__ = ('count',)

    def __init__(self):
        self.count = 0

    def __call__(self):
        count = self.count
        self.count += 1
        return count


class CreationOrderMeta(type):
    """
    A metaclass that assigns a `_creation_order` to class instances
    """

    def __call__(cls, *args, **kwargs):
        ins = super().__call__(*args, **kwargs)
        object.__setattr__(ins, '_creation_order', ins._creation_counter())
        return ins

    def __new__(mcs, name, bases, namespace):
        namespace['_creation_counter'] = Counter()
        return super().__new__(mcs, name, bases, namespace)


class ForgeError(Exception):
    """
    A common base class for ``forge`` exceptions
    """

    pass


class ImmutableInstanceError(ForgeError):
    """
    An error that is raised when trying to set an attribute on a
    :class:`~forge.Immutable` instance.
    """

    pass


def asdict(obj) -> typing.Dict:
    """
    Provides a "look" into any Python class instance by returning a dict
    into the attribute or slot values.

    :param obj: any Python class instance
    :returns: the attribute or slot values from :paramref:`.asdict.obj`
    """
    if hasattr(obj, '__dict__'):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}

    return {k: getattr(obj, k) for k in obj.__slots__ if not k.startswith('_')}


def immutable_replace(obj, **changes):
    """
    Return a new object replacing specified fields with new values.
    class Klass(Immutable):
        def __init__(self, value):
            # in lieu of: self.value = value
            object.__setattr__(self, 'value', value)

    k1 = Klass(1)
    k2 = replace(k1, value=2)
    assert (k1.value, k2.value) == (1, 2)

    :obj: any object who's ``__init__`` method simply writes arguments to
        instance variables
    :changes: an attribute:argument mapping that will replace instance variables
        on the current instance
    """
    return type(obj)(**dict(asdict(obj), **changes))


class Immutable:
    """
    A class whose instances lack a ``__setattr__`` method, making them 99%
    immutable. It's still possible to manipulate the instance variables in
    other ways (as Python doesn't support real immutability outside of
    :class:`collections.namedtuple` or :types.`NamedTuple`).

    :param kwargs: an attribute:argument mapping that are set on the instance
    """

    __slots__ = ()

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            object.__setattr__(self, k, v)

    def __eq__(self, other: typing.Any) -> bool:
        if not isinstance(other, type(self)):
            return False
        return asdict(other) == asdict(self)

    def __getattr__(self, key: str) -> typing.Any:
        """
        Solely for placating mypy.
        Not particularly impressed with this hack but it saves a lot of
        `#type: ignore` effort elsewhere
        """
        return super().__getattribute__(key)

    def __setattr__(self, key: str, value: typing.Any):
        """
        Method exists to inhibit functionality of :func:`setattr`

        :param key: ignored - can't set attributes
        :param value: ignored - can't set attributes
        :raises ImmutableInstanceError: attributes cannot be set on an
            Immutable instance
        """
        raise ImmutableInstanceError("cannot assign to field '{}'".format(key))


class MarkerMeta(type):
    """
    A metaclass that creates marker classes for use as distinguishing elements
    in a signature.
    """

    def __repr__(cls) -> str:
        return '<{}>'.format(cls.__name__)

    def __new__(
        mcs,
        name: str,
        bases: typing.Tuple[type, ...],
        namespace: typing.Dict[str, typing.Any],
    ):
        """
        Create a new ``forge`` marker class with a ``native`` attribute.

        :param name: the name of the new class
        :param bases: the base classes of the new class
        :param namespace: the namespace of the new class
        :param native: the ``native`` Python marker class
        """
        namespace['__repr__'] = lambda self: repr(type(self))
        return super().__new__(mcs, name, bases, namespace)


class void(metaclass=MarkerMeta):
    """
    A simple :class:`~forge.marker.MarkerMeta` class useful for denoting that
    no input was suplied.

    Usage::

        def proxy(a, b, extra=void):
            if extra is not void:
                return proxied(a, b)
            return proxied(a, b, c=extra)
    """

    pass


_void = void()
"""Internal-use void instance"""


class empty(metaclass=MarkerMeta):
    """
    A simple :class:`~forge.marker.MarkerMeta` class useful for denoting that
    no input was suplied. Used in place of :class:`inspect.Parameter.empty`
    as that is not repr'd (providing confusing usage).

    Usage::

        def proxy(a, b, extra=empty):
            if extra is not empty:
                return proxied(a, b)
            return proxied(a, b, c=inspect.Parameter.empty)
    """

    native = inspect.Parameter.empty

    @classmethod
    def ccoerce_native(cls, value):
        """
        Conditionally coerce the value to a non-:class:`~forge.empty` value.

        :param value: the value to conditionally coerce
        :returns: the value, if the value is not an instance of
            :class:`~forge.empty`, otherwise return
            :class:`inspect.Paramter.empty`
        """
        return value if value is not cls else cls.native

    @classmethod
    def ccoerce_synthetic(cls, value):
        """
        Conditionally coerce the value to a
        non-:class:`inspect.Parameter.empty` value.

        :param value: the value to conditionally coerce
        :returns: the value, if the value is not an instance of
            :class:`inspect.Paramter.empty`, otherwise return
            :class:`~forge.empty`
        """
        return value if value is not cls.native else cls


class CallArguments(Immutable):
    """
    An immutable container for call arguments, i.e. term:`var-positional`
    (e.g. ``*args``) and :term:`var-keyword` (e.g. ``**kwargs``).

    :param args: positional arguments used in a call
    :param kwargs: keyword arguments used in a call
    """

    __slots__ = ('args', 'kwargs')

    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        super().__init__(args=args, kwargs=types.MappingProxyType(kwargs))

    def __repr__(self) -> str:
        arguments = ', '.join(
            [
                *[repr(arg) for arg in self.args],
                *['{}={}'.format(k, v) for k, v in self.kwargs.items()],
            ]
        )
        return '<{} ({})>'.format(type(self).__name__, arguments)

    @classmethod
    def from_bound_arguments(
        cls,
        bound: inspect.BoundArguments,
    ) -> 'CallArguments':
        """
        A factory method that creates an instance of
        :class:`~forge._signature.CallArguments` from an instance of
        :class:`instance.BoundArguments` generated from
        :meth:`inspect.Signature.bind` or :meth:`inspect.Signature.bind_partial`

        :param bound: an instance of :class:`inspect.BoundArguments`
        :returns: an unpacked version of :class:`inspect.BoundArguments`
        """
        return cls(*bound.args, **bound.kwargs)

    def to_bound_arguments(
        self,
        signature: inspect.Signature,
        partial: bool = False,
    ) -> inspect.BoundArguments:
        """
        Generates an instance of :class:inspect.BoundArguments` for a given
        :class:`inspect.Signature`.
        Does not raise if invalid or incomplete arguments are provided, as the
        underlying implementation uses :meth:`inspect.Signature.bind_partial`.

        :param signature: an instance of :class:`inspect.Signature` to which
            :paramref:`.CallArguments.args` and
            :paramref:`.CallArguments.kwargs` will be bound.
        :param partial: does not raise if invalid or incomplete arguments are
            provided, as the underlying implementation uses
            :meth:`inspect.Signature.bind_partial`
        :returns: an instance of :class:`inspect.BoundArguments` to which
            :paramref:`.CallArguments.args` and
            :paramref:`.CallArguments.kwargs` are bound.
        """
        return (
            signature.bind_partial(*self.args, **self.kwargs)
            if partial
            else signature.bind(*self.args, **self.kwargs)
        )


def sort_arguments(
    to_: typing.Union[typing.Callable[..., typing.Any], inspect.Signature],
    named: typing.Optional[typing.Dict[str, typing.Any]] = None,
    unnamed: typing.Optional[typing.Iterable] = None,
) -> CallArguments:
    """
    Iterates over the :paramref:`~forge.sort_arguments.named` arguments and
    assinging the values to the parameters with the key as a name.
    :paramref:`~forge.sort_arguments.unnamed` arguments are assigned to the
    :term:`var-positional` parameter.

    Usage:

    .. testcode::

        import forge

        def func(a, b=2, *args, c, d=5, **kwargs):
            return (a, b, args, c, d, kwargs)

        assert forge.callwith(
            func,
            named=dict(a=1, c=4, e=6),
            unnamed=(3,),
        ) == forge.CallArguments(1, 2, 3, c=4, d=5, e=6)

    :param to_: a callable to call with the named and unnamed parameters
    :param named: a mapping of parameter names to argument values.
        Appropriate values are all :term:`positional-only`,
        :term:`positional-or-keyword`, and :term:`keyword-only` arguments,
        as well as additional :term:`var-keyword` mapped arguments which will
        be used to construct the :term:`var-positional` argument on
        :paramref:`~forge.callwith.to_` (if it has such an argument).
        Parameters on :paramref:`~forge.callwith.to_` with default values can
        be ommitted (as expected).
    :param unnamed: an iterable to be passed as the :term:`var-positional`
        parameter. Requires :paramref:`~forge.callwith.to_` to accept
        :term:`var-positional` arguments.
    """
    if not isinstance(to_, inspect.Signature):
        to_ = inspect.signature(to_)
    to_ba = to_.bind_partial()
    to_ba.apply_defaults()

    arguments = named.copy() if named else {}
    vpo_param, vkw_param = None, None

    for name, param in to_.parameters.items():
        if param.kind is inspect.Parameter.VAR_POSITIONAL:
            vpo_param = param
        elif param.kind is inspect.Parameter.VAR_KEYWORD:
            vkw_param = param
        elif name in arguments:
            to_ba.arguments[name] = arguments.pop(name)
            continue
        elif param.default is empty.native:
            raise ValueError("Non-default parameter '{}' has no argument value".format(name))

    if arguments:
        if not vkw_param:
            raise TypeError('Cannot sort arguments ({})'.format(', '.join(arguments.keys())))
        to_ba.arguments[vkw_param.name].update(arguments)

    if unnamed:
        if not vpo_param:
            raise TypeError('Cannot sort var-positional arguments')
        to_ba.arguments[vpo_param.name] = tuple(unnamed)

    return CallArguments.from_bound_arguments(to_ba)


def callwith(
    to_: typing.Callable[..., typing.Any],
    named: typing.Optional[typing.Dict[str, typing.Any]] = None,
    unnamed: typing.Optional[typing.Iterable] = None,
) -> typing.Any:
    """
    Calls and returns the result of :paramref:`~forge.callwith.to_` with the
    supplied ``named`` and ``unnamed`` arguments.

    The arguments and their order as supplied to
    :paramref:`~forge.callwith.to_` is determined by
    iterating over the :paramref:`~forge.callwith.named` arguments and
    assinging the values to the parameters with the key as a name.
    :paramref:`~forge.callwith.unnamed` arguments are assigned to the
    :term:`var-positional` parameter.

    Usage:

    .. testcode::

        import forge

        def func(a, b=2, *args, c, d=5, **kwargs):
            return (a, b, args, c, d, kwargs)

        assert forge.callwith(
            func,
            named=dict(a=1, c=4, e=6),
            unnamed=(3,),
        ) == (1, 2, (3,), 4, 5, {'e': 6})

    :param to_: a callable to call with the named and unnamed parameters
    :param named: a mapping of parameter names to argument values.
        Appropriate values are all :term:`positional-only`,
        :term:`positional-or-keyword`, and :term:`keyword-only` arguments,
        as well as additional :term:`var-keyword` mapped arguments which will
        be used to construct the :term:`var-positional` argument on
        :paramref:`~forge.callwith.to_` (if it has such an argument).
        Parameters on :paramref:`~forge.callwith.to_` with default values can
        be ommitted (as expected).
    :param unnamed: an iterable to be passed as the :term:`var-positional`
        parameter. Requires :paramref:`~forge.callwith.to_` to accept
        :term:`var-positional` arguments.
    """
    call_args = sort_arguments(to_, named, unnamed)
    return to_(*call_args.args, **call_args.kwargs)


def repr_callable(callable: typing.Callable) -> str:
    """
    Build a string representation of a callable, including the callable's
    :attr:``__name__``, its :class:`inspect.Parameter`s and its ``return type``

    usage::

        >>> repr_callable(repr_callable)
        'repr_callable(callable: Callable) -> str'

    :param callable: a Python callable to build a string representation of
    :returns: the string representation of the function
    """
    # pylint: disable=W0622, redefined-builtin
    sig = inspect.signature(callable)
    name = getattr(callable, '__name__', str(callable))
    return '{}{}'.format(name, sig)


class Mapper(Immutable):
    """
    An immutable data structure that provides the recipe for mapping
    an :class:`~forge.FSignature` to an underlying callable.

    :param fsignature: an instance of :class:`~forge.FSignature` that provides
        the public and private interface.
    :param callable: a callable that ultimately receives the arguments provided
        to public :class:`~forge.FSignature` interface.

    :ivar callable: see :paramref:`~forge._signature.Mapper.callable`
    :ivar fsignature: see :paramref:`~forge._signature.Mapper.fsignature`
    :ivar parameter_map: a :class:`types.MappingProxy` that exposes the strategy
        of how to map from the :paramref:`.Mapper.fsignature` to the
        :paramref:`.Mapper.callable`
    :ivar private_signature: a cached copy of
        :paramref:`~forge._signature.Mapper.callable`'s
        :class:`inspect.Signature`
    :ivar public_signature: a cached copy of
        :paramref:`~forge._signature.Mapper.fsignature`'s manifest as a
        :class:`inspect.Signature`
    """

    __slots__ = (
        'callable',
        'context_param',
        'fsignature',
        'parameter_map',
        'private_signature',
        'public_signature',
    )

    def __init__(
        self,
        fsignature: 'FSignature',
        callable: typing.Callable[..., typing.Any],
    ) -> None:
        # pylint: disable=W0622, redefined-builtin
        # pylint: disable=W0621, redefined-outer-name
        private_signature = inspect.signature(callable)
        public_signature = fsignature.native
        parameter_map = self.map_parameters(fsignature, private_signature)
        context_param = get_context_parameter(fsignature)

        super().__init__(
            callable=callable,
            context_param=context_param,
            fsignature=fsignature,
            private_signature=private_signature,
            public_signature=public_signature,
            parameter_map=parameter_map,
        )

    def __call__(self, *args: typing.Any, **kwargs: typing.Any) -> CallArguments:
        """
        Maps the arguments from the :paramref:`~forge.Mapper.public_signature`
        to the :paramref:`~forge.Mapper.private_signature`.

        Follows the strategy:

        #. bind the arguments to the :paramref:`~forge.Mapper.public_signature`
        #. partialy bind the :paramref:`~forge.Mapper.private_signature`
        #. identify the context argument (if one exists) from
        :class:`~forge.FParameter`s on the :class:`~forge.FSignature`
        #. iterate over the intersection of bound arguments and ``bound`` \
        parameters on the :paramref:`.Mapper.fsignature` to the \
        :paramref:`~forge.Mapper.private_signature` of the \
        :paramref:`.Mapper.callable`, getting their transformed value by \
        calling :meth:`~forge.FParameter.__call__`
        #. map the resulting value into the private_signature bound arguments
        #. generate and return a :class:`~forge._signature.CallArguments` from \
        the private_signature bound arguments.

        :param args: the positional arguments to map
        :param kwargs: the keyword arguments to map
        :returns: transformed :paramref:`~forge.Mapper.__call__.args` and
            :paramref:`~forge.Mapper.__call__.kwargs` mapped from
            :paramref:`~forge.Mapper.public_signature` to
            :paramref:`~forge.Mapper.private_signature`
        """
        try:
            public_ba = self.public_signature.bind(*args, **kwargs)
        except TypeError as e:
            raise TypeError(
                '{callable_name}() {message}'.format(
                    callable_name=self.callable.__name__,
                    message=e.args[0],
                ),
            ) from e
        public_ba.apply_defaults()

        private_ba = self.private_signature.bind_partial()
        private_ba.apply_defaults()
        ctx = self.get_context(public_ba.arguments)

        for from_name, from_param in self.fsignature.parameters.items():
            from_val = public_ba.arguments.get(from_name, empty)
            to_name = self.parameter_map[from_name]
            to_param = self.private_signature.parameters[to_name]
            to_val = self.fsignature.parameters[from_name](ctx, from_val)

            if to_param.kind is FParameter.VAR_POSITIONAL:
                # e.g. f(*args) -> g(*args)
                private_ba.arguments[to_name] = to_val
            elif to_param.kind is FParameter.VAR_KEYWORD:
                if from_param.kind is FParameter.VAR_KEYWORD:
                    # e.g. f(**kwargs) -> g(**kwargs)
                    private_ba.arguments[to_name].update(to_val)
                else:
                    # e.g. f(a) -> g(**kwargs)
                    private_ba.arguments[to_name][from_param.interface_name] = to_val
            else:
                # e.g. f(a) -> g(a)
                private_ba.arguments[to_name] = to_val

        return CallArguments.from_bound_arguments(private_ba)

    def __repr__(self) -> str:
        pubstr = str(self.public_signature)
        privstr = str(self.private_signature)
        return '<{} {} => {}>'.format(type(self).__name__, pubstr, privstr)

    def get_context(self, arguments: typing.Mapping) -> typing.Any:
        """
        Retrieves the context arguments value (if a context parameter exists)

        :param arguments: a mapping of parameter names to argument values
        :returns: the argument value for the context parameter (if it exists),
            otherwise ``None``.
        """
        return arguments[self.context_param.name] if self.context_param else None

    @staticmethod
    def map_parameters(
        from_: 'FSignature',
        to_: inspect.Signature,
    ) -> types.MappingProxyType:
        """
        Build a mapping of parameters from the
        :paramref:`.Mapper.map_parameters.from_` to the
        :paramref:`.Mapper.map_parameters.to_`.

        Strategy rules:
        #. every *to_* :term:`positional-only` must be mapped to
        #. every *to_* :term:`positional-or-keyword` w/o default must be
        mapped to
        #. every *to_* :term:`keyword-only` w/o default must be mapped to
        #. *from_* :term:`var-positional` requires *to_* :term:`var-positional`
        #. *from_* :term:`var-keyword` requires *to_* :term:`var-keyword`

        :param from_: the :class:`~forge.FSignature` to map from
        :param to_: the :class:`inspect.Signature` to map to
        :returns: a :class:`types.MappingProxyType` that shows how arguments
            are mapped.
        """
        # pylint: disable=W0622, redefined-builtin
        from_vpo_param = get_var_positional_parameter(from_)
        from_vkw_param = get_var_keyword_parameter(from_)
        from_param_index = {
            fparam.interface_name: fparam
            for fparam in from_
            if fparam not in (from_vpo_param, from_vkw_param)
        }

        to_vpo_param = get_var_positional_parameter(to_.parameters.values())
        to_vkw_param = get_var_keyword_parameter(to_.parameters.values())
        to_param_index = {
            param.name: param
            for param in to_.parameters.values()
            if param not in (to_vpo_param, to_vkw_param)
        }

        mapping = {}
        for name in list(to_param_index):
            param = to_param_index.pop(name)
            try:
                param_t = from_param_index.pop(name)
            except KeyError as e:
                # masked mapping, e.g. f() -> g(a=1)
                if param.default is not empty.native:
                    continue

                # invalid mapping, e.g. f() -> g(a)
                kind_repr = _get_pk_string(param.kind)
                raise TypeError(
                    'Missing requisite mapping to non-default {kind_repr} '
                    "parameter '{pri_name}'".format(kind_repr=kind_repr, pri_name=name)
                ) from e
            else:
                mapping[param_t.name] = name

        if from_vpo_param:
            # invalid mapping, e.g. f(*args) -> g()
            if not to_vpo_param:
                kind_repr = _get_pk_string(FParameter.VAR_POSITIONAL)
                raise TypeError(
                    'Missing requisite mapping from {kind_repr} parameter '
                    "'{from_vpo_param.name}'".format(
                        kind_repr=kind_repr, from_vpo_param=from_vpo_param
                    )
                )
            # var-positional mapping, e.g. f(*args) -> g(*args)
            mapping[from_vpo_param.name] = to_vpo_param.name

        if from_vkw_param:
            # invalid mapping, e.g. f(**kwargs) -> g()
            if not to_vkw_param:
                kind_repr = _get_pk_string(FParameter.VAR_KEYWORD)
                raise TypeError(
                    'Missing requisite mapping from {kind_repr} parameter '
                    "'{from_vkw_param.name}'".format(
                        kind_repr=kind_repr, from_vkw_param=from_vkw_param
                    )
                )
            # var-keyword mapping, e.g. f(**kwargs) -> g(**kwargs)
            mapping[from_vkw_param.name] = to_vkw_param.name

        if from_param_index:
            # invalid mapping, e.g. f(a) -> g()
            if not to_vkw_param:
                raise TypeError(
                    'Missing requisite mapping from parameters ({})'.format(
                        ', '.join([pt.name for pt in from_param_index.values()])
                    )
                )
            # to-var-keyword mapping, e.g. f(a) -> g(**kwargs)
            for param_t in from_param_index.values():
                mapping[param_t.name] = to_vkw_param.name

        return types.MappingProxyType(mapping)


class Revision:
    """
    This is a base class for other revisions.
    It implements two methods of primary importance:
    :meth:`~forge.Revision.revise` and :meth:`~forge.Revision.__call__`.

    Revisions can act as decorators, in which case the callable is wrapped in
    a function that translates the supplied arguments to the parameters the
    underlying callable expects::

        import forge

        @forge.Revision()
        def myfunc():
            pass

    Revisions can also operate on :class:`~forge.FSignature` instances
    directly by providing an ``FSignature`` to :meth:`~forge.Revision.revise`::

        import forge

        in_ = forge.FSignature()
        out_ = forge.Revision().revise(in_)
        assert in_ == out_

    The :meth:`~forge.Revision.revise` method is expected to return an instance
    of :class:`~forge.FSignature` that **is not validated**. This can be
    achieved by supplying ``__validate_attributes__=False`` to either
    :class:`~forge.FSignature` or :meth:`~forge.FSignature.replace`.

    Instances of :class:`~forge.Revision` don't have any initialization
    parameters or public attributes, but subclasses instances often do.
    """

    def __call__(
        self, callable: typing.Callable[..., typing.Any]
    ) -> typing.Callable[..., typing.Any]:
        """
        Wraps a callable with a function that maps the new signature's
        parameters to the original function's signature.

        If the function was already wrapped (has an :attr:`__mapper__`
        attribute), then the (underlying) wrapped function is re-wrapped.

        :param callable: a :term:`callable` whose signature to revise
        :returns: a function with the revised signature that calls into the
            provided :paramref:`~forge.Revision.__call__.callable`
        """
        # pylint: disable=W0622, redefined-builtin
        if hasattr(callable, '__mapper__'):
            next_ = self.revise(callable.__mapper__.fsignature)
            callable = callable.__wrapped__  # type: ignore
        else:
            next_ = self.revise(FSignature.from_callable(callable))

        # Unrevised; not wrapped
        if asyncio.iscoroutinefunction(callable):

            @functools.wraps(callable)
            async def inner(*args, **kwargs):
                # pylint: disable=E1102, not-callable
                mapped = inner.__mapper__(*args, **kwargs)
                return await callable(*mapped.args, **mapped.kwargs)
        else:

            @functools.wraps(callable)
            def inner(*args, **kwargs):
                # pylint: disable=E1102, not-callable
                mapped = inner.__mapper__(*args, **kwargs)
                return callable(*mapped.args, **mapped.kwargs)

        next_.validate()
        inner.__mapper__ = Mapper(next_, callable)  # type: ignore
        inner.__signature__ = inner.__mapper__.public_signature  # type: ignore
        return inner

    def revise(self, previous: 'FSignature') -> 'FSignature':
        """
        Applies the identity revision: ``previous`` is returned unmodified.

        No validation is performed on the updated :class:`~forge.FSignature`,
        allowing it to be used as an intermediate revision in the context of
        :class:`~forge.compose`.

        :param previous: the :class:`~forge.FSignature` to modify
        :returns: a modified instance of :class:`~forge.FSignature`
        """
        # pylint: disable=R0201, no-self-use
        return previous


## Group Revisions
class compose(Revision):  # pylint: disable=C0103, invalid-name
    """
    Batch revision that takes :class:`~forge.Revision` instances and applies
    their :meth:`~forge.Revision.revise` using :func:`functools.reduce`.

    :param revisions: instances of :class:`~forge.Revision`, used to revise
        the :class:`~forge.FSignature`.
    """

    def __init__(self, *revisions):
        for rev in revisions:
            if not isinstance(rev, Revision):
                raise TypeError("received non-revision '{}'".format(rev))
        self.revisions = revisions

    def revise(self, previous: 'FSignature') -> 'FSignature':
        """
        Applies :paramref:`~forge.compose.revisions`

        No validation is explicitly performed on the updated
        :class:`~forge.FSignature`, allowing it to be used as an intermediate
        revision in the context of (another) :class:`~forge.compose`.

        :param previous: the :class:`~forge.FSignature` to modify
        :returns: a modified instance of :class:`~forge.FSignature`
        """
        return functools.reduce(
            lambda previous, revision: revision.revise(previous),
            self.revisions,
            previous,
        )


class copy(Revision):  # pylint: disable=C0103, invalid-name
    """
    The ``copy`` revision takes a :term:`callable` and optionally parameters to
    include or exclude, and applies the resultant signature.

    :param callable: a callable whose signature is copied
    :param include: a string, iterable of strings, or a function that receives
        an instance of :class:`~forge.FParameter` and returns a truthy value
        whether to include it.
    :param exclude: a string, iterable of strings, or a function that receives
        an instance of :class:`~forge.FParameter` and returns a truthy value
        whether to exclude it.
    :raises TypeError: if ``include`` and ``exclude`` are provided
    """

    def __init__(
        self,
        callable: typing.Callable[..., typing.Any],
        *,
        include: typing.Optional['_TYPE_FINDITER_SELECTOR'] = None,
        exclude: typing.Optional['_TYPE_FINDITER_SELECTOR'] = None,
    ) -> None:
        # pylint: disable=W0622, redefined-builtin
        if include is not None and exclude is not None:
            raise TypeError("expected 'include', 'exclude', or neither, but received both")

        self.signature = fsignature(callable)
        self.include = include
        self.exclude = exclude

    def revise(self, previous: 'FSignature') -> 'FSignature':
        """
        Copies the signature of :paramref:`~forge.copy.callable`.
        If provided, only a subset of parameters are copied, as determiend by
        :paramref:`~forge.copy.include` and :paramref:`~forge.copy.exclude`.

        Unlike most subclasses of :class:`~forge.Revision`, validation is
        performed on the updated :class:`~forge.FSignature`.
        This is because :class:`~forge.copy` takes a :term:`callable` which
        is required by Python to have a valid signature, so it's impossible
        to return an invalid signature.

        :param previous: the :class:`~forge.FSignature` to modify
        :returns: a modified instance of :class:`~forge.FSignature`
        """
        if self.include:
            return self.signature.replace(parameters=list(findparam(self.signature, self.include)))
        elif self.exclude:
            excluded = list(findparam(self.signature, self.exclude))
            return self.signature.replace(
                parameters=[param for param in self.signature if param not in excluded]
            )
        return self.signature


class manage(Revision):  # pylint: disable=C0103, invalid-name
    """
    Revision that revises a :class:`~forge.FSignature` with a user-supplied
    revision function.

    .. testcode::

        import forge

        def reverse(previous):
            return previous.replace(
                parameters=previous[::-1],
                __validate_parameters__=False,
            )

        @forge.manage(reverse)
        def func(a, b, c):
            pass

        assert forge.repr_callable(func) == 'func(c, b, a)'

    :param callable: a callable that alters the previous signature
    """

    def __init__(self, callable: typing.Callable[['FSignature'], 'FSignature']) -> None:
        # pylint: disable=W0622, redefined-builtin
        self.callable = callable

    def revise(self, previous: 'FSignature') -> 'FSignature':
        """
        Passes the signature to :paramref:`~forge.manage.callable` for
        revision.

        .. warning::

            No validation is typically performed in the :attr:`revise` method.
            Consider providing `False` as an argument value to
            :paramref:`~forge.FSignature.__validate_parameters__`, so that this
            revision can be used within the context of a
            :class:`~forge.compose` revision.

        :param previous: the :class:`~forge.FSignature` to modify
        :returns: a modified instance of :class:`~forge.FSignature`
        """
        return self.callable(previous)


class returns(Revision):  # pylint: disable=invalid-name
    """
    The ``returns`` revision updates a signature's ``return-type`` annotation.

    .. testcode::

        import forge

        @forge.returns(int)
        def x():
            pass

        assert forge.repr_callable(x) == "x() -> int"

    :param type: the ``return type`` for the factory
    :ivar return_annotation: the ``return type`` used for revising signatures
    """

    def __init__(self, type: typing.Any = empty) -> None:
        # pylint: disable=W0622, redefined-builtin
        self.return_annotation = type

    def __call__(
        self, callable: typing.Callable[..., typing.Any]
    ) -> typing.Callable[..., typing.Any]:
        """
        Changes the return value of the supplied callable.
        If the callable is already revised (has an
        :attr:`__mapper__` attribute), then the ``return type`` annoation is
        set without wrapping the function.
        Otherwise, the :attr:`__mapper__` and :attr:`__signature__` are updated

        :param callable: see :paramref:`~forge.Revision.__call__.callable`
        :returns: either the input callable with an updated return type
            annotation, or a wrapping function with the appropriate return type
            annotation as determined by the strategy described above.
        """
        # pylint: disable=W0622, redefined-builtin
        if hasattr(callable, '__mapper__'):
            return super().__call__(callable)

        elif hasattr(callable, '__signature__'):
            sig = callable.__signature__
            callable.__signature__ = sig.replace(return_annotation=self.return_annotation)

        else:
            callable.__annotations__['return'] = self.return_annotation

        return callable

    def revise(self, previous: 'FSignature') -> 'FSignature':
        """
        Applies the return type annotation,
        :paramref:`~forge.returns.return_annotation`, to the input signature.

        No validation is performed on the updated :class:`~forge.FSignature`,
        allowing it to be used as an intermediate revision in the context of
        :class:`~forge.compose`.

        :param previous: the :class:`~forge.FSignature` to modify
        :returns: a modified instance of :class:`~forge.FSignature`
        """
        return FSignature(
            previous,
            return_annotation=self.return_annotation,
        )


class synthesize(Revision):  # pylint: disable=C0103, invalid-name
    """
    Revision that builds a new signature from instances of
    :class:`~forge.FParameter`

    Order parameters with the following strategy:

    #. arguments are returned in order
    #. keyword arguments are sorted by ``_creation_order``, and evolved with \
    the ``keyword`` value as the name and interface_name (if not set).

    .. warning::

        When supplying previously-created parameters to :func:`~forge.sign`,
        those parameters will be ordered by their creation order.

        This is because Python implementations prior to ``3.7`` don't
        guarantee the ordering of keyword-arguments.

        Therefore, it is recommended that when supplying pre-created
        parameters to :func:`~forge.sign`, you supply them as positional
        arguments:

        .. testcode::

            import forge

            param_b = forge.arg('b')
            param_a = forge.arg('a')

            @forge.sign(a=param_a, b=param_b)
            def func1(**kwargs):
                pass

            @forge.sign(param_a, param_b)
            def func2(**kwargs):
                pass

            assert forge.repr_callable(func1) == 'func1(b, a)'
            assert forge.repr_callable(func2) == 'func2(a, b)'

    :param parameters: :class:`~forge.FParameter` instances to be ordered
    :param named_parameters: :class:`~forge.FParameter` instances to be
        ordered, updated
    :returns: a wrapping factory that takes a callable and returns a wrapping
        function that has a signature as defined by the
        :paramref:`~forge.synthesize..parameters` and
        :paramref:`~forge.synthesize.named_parameters`
    """

    def __init__(self, *parameters, **named_parameters):
        self.parameters = [
            *parameters,
            *[
                param.replace(
                    name=name,
                    interface_name=param.interface_name or name,
                )
                for name, param in sorted(
                    named_parameters.items(),
                    key=lambda i: i[1]._creation_order,
                )
            ],
        ]

    def revise(self, previous: 'FSignature') -> 'FSignature':
        """
        Produces a signature with the parameters provided at initialization.

        No validation is performed on the updated :class:`~forge.FSignature`,
        allowing it to be used as an intermediate revision in the context of
        :class:`~forge.compose`.

        :param previous: the :class:`~forge.FSignature` to modify
        :returns: a modified instance of :class:`~forge.FSignature`
        """
        return previous.replace(
            parameters=self.parameters,
            __validate_parameters__=False,
        )


# Convenience name
sign = synthesize  # pylint: disable=C0103, invalid-name


class sort(Revision):  # pylint: disable=C0103, invalid-name
    """
    Revision that orders parameters. The default orders parameters ina common-
    sense way:

    #. :term:`parameter kind`, then
    #. parameters having a default value
    #. parameter name lexicographically

    .. testcode::

        import forge

        @forge.sort()
        def func(c, b, a):
            pass

        assert forge.repr_callable(func) == 'func(a, b, c)'

    :param sortkey: a function provided to the builtin :func:`sorted`.
        Receives instances of :class:`~forge.FParameter`, and should return a
        key to sort on.
    """

    @staticmethod
    def _sortkey(param):
        """
        Default sortkey for :meth:`~forge.sort.revise` that orders by:

        #. :term:`parameter kind`, then
        #. parameters having a default value
        #. parameter name lexicographically

        :returns: tuple to sort by
        """
        return (param.kind, param.default is not empty, param.name or '')

    def __init__(
        self, sortkey: typing.Optional[typing.Callable[['FParameter'], typing.Any]] = None
    ) -> None:
        self.sortkey = sortkey or self._sortkey

    def revise(self, previous: 'FSignature') -> 'FSignature':
        """
        Applies the sorting :paramref:`~forge.returns.return_annotation`, to
        the input signature.

        No validation is performed on the updated :class:`~forge.FSignature`,
        allowing it to be used as an intermediate revision in the context of
        :class:`~forge.compose`.

        :param previous: the :class:`~forge.FSignature` to modify
        :returns: a modified instance of :class:`~forge.FSignature`
        """
        return previous.replace(
            parameters=sorted(previous, key=self.sortkey),
            __validate_parameters__=False,
        )


## Unit Revisions
class delete(Revision):  # pylint: disable=C0103, invalid-name
    """
    Revision that deletes one (or more) parameters from an
    :class:`~forge.FSignature`.

    :param selector: a string, iterable of strings, or a function that
        receives an instance of :class:`~forge.FParameter` and returns a
        truthy value whether to exclude it.
    :param multiple: whether to delete all parameters that match the
        ``selector``
    :param raising: whether to raise an exception if the ``selector`` matches
        no parameters
    """

    def __init__(
        self, selector: '_TYPE_FINDITER_SELECTOR', multiple: bool = False, raising: bool = True
    ) -> None:
        self.selector = selector
        self.multiple = multiple
        self.raising = raising

    def revise(self, previous: 'FSignature') -> 'FSignature':
        """
        Deletes one or more parameters from ``previous`` based on instance
        attributes.

        No validation is performed on the updated :class:`~forge.FSignature`,
        allowing it to be used as an intermediate revision in the context of
        :class:`~forge.compose`.

        :param previous: the :class:`~forge.FSignature` to modify
        :returns: a modified instance of :class:`~forge.FSignature`
        """
        excluded = list(findparam(previous, self.selector))
        if not excluded:
            if self.raising:
                raise ValueError("No parameter matched selector '{}'".format(self.selector))
            return previous

        if not self.multiple:
            del excluded[1:]

        return previous.replace(
            parameters=[param for param in previous if param not in excluded],
            __validate_parameters__=False,
        )


class insert(Revision):  # pylint: disable=C0103, invalid-name
    """
    Revision that inserts a new parameter into a signature at an index,
    before a selector, or after a selector.

    .. testcode::

        import forge

        @forge.insert(forge.arg('a'), index=0)
        def func(b, **kwargs):
            pass

        assert forge.repr_callable(func) == 'func(a, b, **kwargs)'

    :param insertion: the parameter or iterable of parameters to insert
    :param index: the index to insert the parameter into the signature
    :param before: a string, iterable of strings, or a function that
        receives an instance of :class:`~forge.FParameter` and returns a
        truthy value whether to place the provided parameter before it.
    :param after: a string, iterable of strings, or a function that
        receives an instance of :class:`~forge.FParameter` and returns a
        truthy value whether to place the provided parameter before it.
    """

    def __init__(
        self,
        insertion: typing.Union['FParameter', typing.Iterable['FParameter']],
        *,
        index: typing.Optional[int] = None,
        before: typing.Optional['_TYPE_FINDITER_SELECTOR'] = None,
        after: typing.Optional['_TYPE_FINDITER_SELECTOR'] = None,
    ) -> None:
        provided = dict(
            filter(
                lambda i: i[1] is not None,
                {'index': index, 'before': before, 'after': after}.items(),
            )
        )
        if not provided:
            raise TypeError("expected keyword argument 'index', 'before', or 'after'")
        elif len(provided) > 1:
            raise TypeError("expected 'index', 'before' or 'after' received multiple")

        self.insertion = [insertion] if isinstance(insertion, FParameter) else list(insertion)
        self.index = index
        self.before = before
        self.after = after

    def revise(self, previous: 'FSignature') -> 'FSignature':
        """
        Inserts the :paramref:`~forge.insert.insertion` into a signature.

        No validation is performed on the updated :class:`~forge.FSignature`,
        allowing it to be used as an intermediate revision in the context of
        :class:`~forge.compose`.

        :param previous: the :class:`~forge.FSignature` to modify
        :returns: a modified instance of :class:`~forge.FSignature`
        """
        pparams = list(previous)
        nparams = []
        if self.before:
            try:
                match = next(findparam(pparams, self.before))
            except StopIteration as e:
                raise ValueError("No parameter matched selector '{}'".format(self.before)) from e

            for param in pparams:
                if param is match:
                    nparams.extend(self.insertion)
                nparams.append(param)
        elif self.after:
            try:
                match = next(findparam(pparams, self.after))
            except StopIteration as e:
                raise ValueError("No parameter matched selector '{}'".format(self.after)) from e

            for param in previous:
                nparams.append(param)
                if param is match:
                    nparams.extend(self.insertion)
        else:
            nparams = pparams[: self.index] + self.insertion + pparams[self.index :]

        return previous.replace(
            parameters=nparams,
            __validate_parameters__=False,
        )


class modify(Revision):  # pylint: disable=C0103, invalid-name
    """
    Revision that modifies one or more parameters.

    .. testcode::

        import forge

        @forge.modify('a', kind=forge.FParameter.POSITIONAL_ONLY)
        def func(a):
            pass

        assert forge.repr_callable(func) == 'func(a, /)'

    :param selector: a string, iterable of strings, or a function that
        receives an instance of :class:`~forge.FParameter` and returns a
        truthy value whether to place the provided parameter before it.
    :param multiple: whether to delete all parameters that match the
        ``selector``
    :param raising: whether to raise an exception if the ``selector`` matches
        no parameters
    :param kind: see :paramref:`~forge.FParameter.kind`
    :param name: see :paramref:`~forge.FParameter.name`
    :param interface_name: see :paramref:`~forge.FParameter.interface_name`
    :param default: see :paramref:`~forge.FParameter.default`
    :param factory: see :paramref:`~forge.FParameter.factory`
    :param type: see :paramref:`~forge.FParameter.type`
    :param converter: see :paramref:`~forge.FParameter.converter`
    :param validator: see :paramref:`~forge.FParameter.validator`
    :param bound: see :paramref:`~forge.FParameter.bound`
    :param contextual: see :paramref:`~forge.FParameter.contextual`
    :param metadata: see :paramref:`~forge.FParameter.metadata`
    """

    def __init__(
        self,
        selector: '_TYPE_FINDITER_SELECTOR',
        multiple: bool = False,
        raising: bool = True,
        *,
        kind=_void,
        name=_void,
        interface_name=_void,
        default=_void,
        factory=_void,
        type=_void,
        converter=_void,
        validator=_void,
        bound=_void,
        contextual=_void,
        metadata=_void,
    ) -> None:
        # pylint: disable=W0622, redefined-builtin
        # pylint: disable=R0914, too-many-locals
        self.selector = selector
        self.multiple = multiple
        self.raising = raising
        self.updates = {
            k: v
            for k, v in {
                'kind': kind,
                'name': name,
                'interface_name': interface_name,
                'default': default,
                'factory': factory,
                'type': type,
                'converter': converter,
                'validator': validator,
                'bound': bound,
                'contextual': contextual,
                'metadata': metadata,
            }.items()
            if v is not _void
        }

    def revise(self, previous: 'FSignature') -> 'FSignature':
        """
        Revises one or more parameters that matches
        :paramref:`~forge.modify.selector`.

        No validation is performed on the updated :class:`~forge.FSignature`,
        allowing it to be used as an intermediate revision in the context of
        :class:`~forge.compose`.

        :param previous: the :class:`~forge.FSignature` to modify
        :returns: a modified instance of :class:`~forge.FSignature`
        """
        matched = list(findparam(previous, self.selector))
        if not matched:
            if self.raising:
                raise ValueError("No parameter matched selector '{}'".format(self.selector))
            return previous

        if not self.multiple:
            del matched[1:]

        return previous.replace(
            parameters=[
                param.replace(**self.updates) if param in matched else param for param in previous
            ],
            __validate_parameters__=False,
        )


class replace(Revision):  # pylint: disable=C0103, invalid-name
    """
    Revision that replaces a parameter.

    .. testcode::

        import forge

        @forge.replace('a', forge.kwo('b', 'a'))
        def func(a):
            pass

        assert forge.repr_callable(func) == 'func(*, b)'

    :param selector: a string, iterable of strings, or a function that
        receives an instance of :class:`~forge.FParameter` and returns a
        truthy value whether to place the provided parameter before it.
    :param parameter: an instance of :class:`~forge.FParameter` to replace
        the selected parameter with.
    """

    def __init__(self, selector: '_TYPE_FINDITER_SELECTOR', parameter: 'FParameter') -> None:
        self.selector = selector
        self.parameter = parameter

    def revise(self, previous: 'FSignature') -> 'FSignature':
        """
        Replaces a parameter that matches
        :paramref:`~forge.replace.selector`.

        No validation is performed on the updated :class:`~forge.FSignature`,
        allowing it to be used as an intermediate revision in the context of
        :class:`~forge.compose`.

        :param previous: the :class:`~forge.FSignature` to modify
        :returns: a modified instance of :class:`~forge.FSignature`
        """
        try:
            match = next(findparam(previous, self.selector))
        except StopIteration as e:
            raise ValueError("No parameter matched selector '{}'".format(self.selector)) from e

        return previous.replace(
            parameters=[self.parameter if param is match else param for param in previous],
            __validate_parameters__=False,
        )


class translocate(Revision):  # pylint: disable=C0103, invalid-name
    """
    Revision that translocates (moves) a parameter to a new position in a
    signature.

    .. testcode::

        import forge

        @forge.translocate('a', index=1)
        def func(a, b):
            pass

        assert forge.repr_callable(func) == 'func(b, a)'

    :param selector: a string, iterable of strings, or a function that
        receives an instance of :class:`~forge.FParameter` and returns a
        truthy value whether to place the provided parameter before it.
    :param index: the index to insert the parameter into the signature
    :param before: a string, iterable of strings, or a function that
        receives an instance of :class:`~forge.FParameter` and returns a
        truthy value whether to place the provided parameter before it.
    :param after: a string, iterable of strings, or a function that
        receives an instance of :class:`~forge.FParameter` and returns a
        truthy value whether to place the provided parameter before it.
    """

    def __init__(self, selector, *, index=None, before=None, after=None):
        provided = dict(
            filter(
                lambda i: i[1] is not None,
                {'index': index, 'before': before, 'after': after}.items(),
            )
        )
        if not provided:
            raise TypeError("expected keyword argument 'index', 'before', or 'after'")
        elif len(provided) > 1:
            raise TypeError("expected 'index', 'before' or 'after' received multiple")

        self.selector = selector
        self.index = index
        self.before = before
        self.after = after

    def revise(self, previous: 'FSignature') -> 'FSignature':
        """
        Translocates (moves) the :paramref:`~forge.insert.parameter` into a
        new position in the signature.

        No validation is performed on the updated :class:`~forge.FSignature`,
        allowing it to be used as an intermediate revision in the context of
        :class:`~forge.compose`.

        :param previous: the :class:`~forge.FSignature` to modify
        :returns: a modified instance of :class:`~forge.FSignature`
        """
        try:
            selected = next(findparam(previous, self.selector))
        except StopIteration as e:
            raise ValueError("No parameter matched selector '{}'".format(self.selector)) from e

        if self.before:
            try:
                before = next(findparam(previous, self.before))
            except StopIteration as e:
                raise ValueError("No parameter matched selector '{}'".format(self.before)) from e

            parameters = []
            for param in previous:
                if param is before:
                    parameters.append(selected)
                elif param is selected:
                    continue
                parameters.append(param)
        elif self.after:
            try:
                after = next(findparam(previous, self.after))
            except StopIteration as e:
                raise ValueError("No parameter matched selector '{}'".format(self.after)) from e

            parameters = []
            for param in previous:
                if param is not selected:
                    parameters.append(param)
                if param is after:
                    parameters.append(selected)
        else:
            parameters = [param for param in previous if param is not selected]
            parameters.insert(self.index, selected)

        return previous.replace(
            parameters=parameters,
            __validate_parameters__=False,
        )


# Convenience name
move = translocate  # pylint: disable=C0103, invalid-name


## Parameter
POSITIONAL_ONLY = inspect.Parameter.POSITIONAL_ONLY
POSITIONAL_OR_KEYWORD = inspect.Parameter.POSITIONAL_OR_KEYWORD
VAR_POSITIONAL = inspect.Parameter.VAR_POSITIONAL
KEYWORD_ONLY = inspect.Parameter.KEYWORD_ONLY
VAR_KEYWORD = inspect.Parameter.VAR_KEYWORD

_PARAMETER_KIND_STRINGS = {
    inspect.Parameter.POSITIONAL_ONLY: 'positional only',
    inspect.Parameter.POSITIONAL_OR_KEYWORD: 'positional or keyword',
    inspect.Parameter.VAR_POSITIONAL: 'variable positional',
    inspect.Parameter.KEYWORD_ONLY: 'keyword only',
    inspect.Parameter.VAR_KEYWORD: 'variable keyword',
}
_get_pk_string = _PARAMETER_KIND_STRINGS.__getitem__


class Factory(Immutable):
    """
    A Factory object is a wrapper around a callable that gets called to generate
    a default value everytime a function is invoked.

    :param factory: a callable which is invoked without argument to generate
        a default value.
    """

    __slots__ = ('factory',)

    def __init__(self, factory: typing.Callable[[], typing.Any]) -> None:
        # pylint: disable=C0102, blacklisted-name
        super().__init__(factory=factory)

    def __repr__(self) -> str:
        return '<{} {}>'.format(type(self).__name__, self.factory.__qualname__)

    def __call__(self) -> typing.Any:
        return self.factory()


class FParameter(Immutable, metaclass=CreationOrderMeta):
    """
    An immutable representation of a signature parameter that encompasses its
    public name, its interface name, transformations to be applied, and
    associated meta-data that defines its behavior in a signature.

    .. note::

        This class doesn't need to be invoked directly. Use one of the
        constructor methods instead:

        - :func:`~forge.pos` for :term:`positional-only` \
        :class:`~forge.FParameter`
        - :func:`~forge.pok` *or* :func:`~forge.arg` for \
        :term:`positional-or-keyword` :class:`~forge.FParameter`
        - :func:`~forge.vpo` for :term:`var-positional` \
        :class:`~forge.FParameter`
        - :func:`~forge.kwo` *or* :func:`~forge.kwarg` for \
        :term:`keyword-only` :class:`~forge.FParameter`
        - :func:`~forge.vkw` for :term:`var-keyword` :class:`~forge.FParameter`

    :param kind: the :term:`parameter kind`, which detemrines the position
        of the parameter in a callable signature.
    :param name: the public name of the parameter.
        For example, in :code:`f(x)` -> :code:`g(y)`, ``name`` is ``x``.
    :param interface_name: the name of mapped-to the parameter.
        For example, in :code:`f(x)` -> :code:`g(y)`,
        ``interface_name`` is ``y``.
    :param default: the default value for the parameter.
        Cannot be supplied alongside a ``factory`` argument.
        For example, to achieve :code:`f(x=3)`, specify :code`default=3`.
    :param factory: a function that generates a default for the parameter
        Cannot be supplied alongside a ``default`` argument.
        For example, to achieve :code:`f(x=<Factory now>)`,
        specify :code:`factory=default.now` (notice: without parentheses).
    :param type: the type annotation of the parameter.
        For example, to achieve :code:`f(x: int)`, ``type`` is ``int``.
    :param converter: a callable or iterable of callables that receive a
        ``ctx`` argument, a ``name`` argument and a ``value`` argument
        for transforming inputs.
    :param validator: a callable that receives a ``ctx`` argument,
        a ``name`` argument and a ``value`` argument for validating inputs.
    :param bound: whether the parameter is visible in the signature
        (requires ``default`` or ``factory`` if True)
    :param contextual: whether the parameter will be passed to
        ``converter`` and ``validator`` callables as the context
        (only the first parameter in a :class:`~forge.FSignature` can be
        contextual)
    :param metadata: optional, extra meta-data that describes the parameter

    :cvar POSITIONAL_ONLY: the :term:`positional-only`
        :term:`parameter kind` constant
        :attr:`inspect.Parameter.POSITIONAL_ONLY`
    :cvar POSITIONAL_OR_KEYWORD: the :term:`positional-or-keyword`
        :term:`parameter kind` constant
        :attr:`inspect.Parameter.POSITIONAL_OR_KEYWORD`
    :cvar VAR_POSITIONAL: the :term:`var-positional` constant
        :term:`parameter kind` constant
        :attr:`inspect.Parameter.VAR_POSITIONAL`
    :cvar KEYWORD_ONLY: the :term:`keyword-only` constant
        :term:`parameter kind` constant
        :attr:`inspect.Parameter.KEYWORD_ONLY`
    :cvar VAR_KEYWORD: the :term:`var-keyword` constant
        :term:`parameter kind` constant
        :attr:`inspect.Parameter.VAR_KEYWORD`
    """

    __slots__ = (
        '_creation_order',
        'kind',
        'name',
        'interface_name',
        'default',
        'type',
        'converter',
        'validator',
        'bound',
        'contextual',
        'metadata',
    )

    empty = empty
    POSITIONAL_ONLY = POSITIONAL_ONLY
    POSITIONAL_OR_KEYWORD = POSITIONAL_OR_KEYWORD
    VAR_POSITIONAL = VAR_POSITIONAL
    KEYWORD_ONLY = KEYWORD_ONLY
    VAR_KEYWORD = VAR_KEYWORD

    def __init__(
        self,
        kind: _TYPE_FP_KIND,
        name: _TYPE_FP_NAME = None,
        interface_name: _TYPE_FP_NAME = None,
        default: _TYPE_FP_DEFAULT = empty,
        factory: _TYPE_FP_FACTORY = empty,
        type: _TYPE_FP_TYPE = empty,
        converter: _TYPE_FP_CONVERTER = None,
        validator: _TYPE_FP_VALIDATOR = None,
        bound: _TYPE_FP_BOUND = False,
        contextual: _TYPE_FP_CONTEXTUAL = False,
        metadata: typing.Optional[_TYPE_FP_METADATA] = None,
    ) -> None:
        # pylint: disable=W0622, redefined-builtin
        # pylint: disable=R0913, too-many-arguments
        if name is not None and not isinstance(name, str):
            # Do enough validation of name to enable the Sequence functionality
            # of FSignature
            raise TypeError(
                'name must be a str, not a {}'.format(name),
            )

        if interface_name is not None and not isinstance(interface_name, str):
            raise TypeError('interface_name must be a str, not a {}'.format(interface_name))

        if factory is not empty:
            if default is not empty:
                raise TypeError('expected either "default" or "factory", received both')
            default = Factory(factory)

        if bound and default is empty:
            raise TypeError('bound arguments must have a default value')

        super().__init__(
            kind=kind,
            name=name or interface_name,
            interface_name=interface_name or name,
            default=default,
            type=type,
            converter=converter,
            validator=validator,
            contextual=contextual,
            bound=bound,
            metadata=types.MappingProxyType(metadata or {}),
        )

    def __str__(self) -> str:
        """
        Generates a string representation of the :class:`~forge.FParameter`
        """
        if self.kind == self.VAR_POSITIONAL:
            prefix = '*'
        elif self.kind == self.VAR_KEYWORD:
            prefix = '**'
        else:
            prefix = ''

        mapped = (
            '{prefix}{name}'.format(
                prefix=prefix,
                name=self.name or '<missing>',
            )
            if self.name == self.interface_name
            else '{prefix}{name}->{prefix}{interface_name}'.format(
                prefix=prefix,
                name=self.name or '<missing>',
                interface_name=self.interface_name or '<missing>',
            )
        )

        annotated = (
            mapped
            if self.type is empty
            else '{mapped}:{annotation}'.format(
                mapped=mapped,
                annotation=self.type.__name__ if inspect.isclass(self.type) else str(self.type),
            )
        )

        return (
            annotated
            if self.default is empty
            else '{annotated}={default}'.format(
                annotated=annotated,
                default=self.default,
            )
        )

    def __repr__(self) -> str:
        return '<{} "{}">'.format(type(self).__name__, str(self))

    def apply_default(self, value: typing.Any) -> typing.Any:
        """
        Return the argument value (if not :class:`~forge.empty`), or the value
        from :paramref:`~forge.FParmeter.default` (if not an instance of
        :class:`~forge.Factory`), or the value obtained by calling
        :paramref:`~forge.FParameter.default` (if an instance of
        :class:`~forge.Factory`).

        :param value: the argument value for this parameter
        :returns: the input value or a default value
        """
        if value is not empty:
            return value() if isinstance(value, Factory) else value
        return self.default

    def apply_conversion(
        self,
        ctx: typing.Any,
        value: typing.Any,
    ) -> typing.Any:
        """
        Apply a transform or series of transforms against the argument value
        with the callables from :paramref:`~forge.FParameter.converter`.

        :param ctx: the context of this parameter as provided by the
            :class:`~forge.FSignature` (typically self or ctx).
        :param value: the argument value for this parameter
        :returns: the converted value
        """
        # pylint: disable=W0621, redefined-outer-name
        if self.converter is None:
            return value
        elif isinstance(self.converter, typing.Iterable):
            return functools.reduce(
                lambda val, func: func(ctx, self.name, val),
                [value, *self.converter],
            )
        return self.converter(ctx, self.name, value)

    def apply_validation(
        self,
        ctx: typing.Any,
        value: typing.Any,
    ) -> typing.Any:
        """
        Apply a validation or series of validations against the argument value
        with the callables from :paramref:`~forge.FParameter.validator`.

        :param ctx: the context of this parameter as provided by the
            :class:`~forge.FSignature` (typically self or ctx).
        :param value: the value the user has supplied or a default value
        :returns: the (unchanged) validated value
        """
        # pylint: disable=W0621, redefined-outer-name
        if isinstance(self.validator, typing.Iterable):
            for validate in self.validator:
                validate(ctx, self.name, value)
        elif self.validator is not None:
            self.validator(ctx, self.name, value)
        return value

    def __call__(self, ctx: typing.Any, value: typing.Any) -> typing.Any:
        """
        Can be called after defaults have been applied (if not a ``bound``
        :class:`~forge.FParameter`) or without a value (i.e.
        :class:`inspect.Parameter.emtpy`) in the case of a ``bound``
        :class:`~forge.FParameter`.

        Process:

        - conditionally apply the :class:`~forge.Factory`,
        - convert the resulting value with the \
        :paramref:`~forge.FParameter.converter`, and then
        - validate the resulting value with the \
        :forge:`~forge.FParameter.validator`.

        :param ctx: the context of this parameter as provided by the
            :class:`~forge.FSignature` (typically self or ctx).
        :param value: the user-supplied (or default) value
        """
        # pylint: disable=W0621, redefined-outer-name
        defaulted = self.apply_default(value)
        converted = self.apply_conversion(ctx, defaulted)
        return self.apply_validation(ctx, converted)

    @property
    def native(self) -> inspect.Parameter:
        """
        A native representation of this :class:`~forge.FParameter` as an
        :class:`inspect.Parameter`, fit for an instance of
        :class:`inspect.Signature`
        """
        if not self.name:
            raise TypeError('Cannot generate an unnamed parameter')
        return inspect.Parameter(
            name=self.name,
            kind=self.kind,
            default=empty.ccoerce_native(self.default),
            annotation=empty.ccoerce_native(self.type),
        )

    def replace(
        self,
        *,
        kind=_void,
        name=_void,
        interface_name=_void,
        default=_void,
        factory=_void,
        type=_void,
        converter=_void,
        validator=_void,
        bound=_void,
        contextual=_void,
        metadata=_void,
    ):
        """
        An evolution method that generates a new :class:`~forge.FParameter`
        derived from this instance and the provided updates.

        :param kind: see :paramref:`~forge.FParameter.kind`
        :param name: see :paramref:`~forge.FParameter.name`
        :param interface_name: see :paramref:`~forge.FParameter.interface_name`
        :param default: see :paramref:`~forge.FParameter.default`
        :param factory: see :paramref:`~forge.FParameter.factory`
        :param type: see :paramref:`~forge.FParameter.type`
        :param converter: see :paramref:`~forge.FParameter.converter`
        :param validator: see :paramref:`~forge.FParameter.validator`
        :param bound: see :paramref:`~forge.FParameter.bound`
        :param contextual: see :paramref:`~forge.FParameter.contextual`
        :param metadata: see :paramref:`~forge.FParameter.metadata`
        :returns: an instance of `~forge.FParameter`
        """
        # pylint: disable=E1120, no-value-for-parameter
        # pylint: disable=W0622, redefined-builtin
        # pylint: disable=R0913, too-many-arguments
        if factory is not _void and default is _void:
            default = empty

        return immutable_replace(
            self,
            **{
                k: v
                for k, v in {
                    'kind': kind,
                    'name': name,
                    'interface_name': interface_name,
                    'default': default,
                    'factory': factory,
                    'type': type,
                    'converter': converter,
                    'validator': validator,
                    'bound': bound,
                    'contextual': contextual,
                    'metadata': metadata,
                }.items()
                if v is not _void
            },
        )

    @classmethod
    def from_native(cls, native: inspect.Parameter) -> 'FParameter':
        """
        A factory method for creating :class:`~forge.FParameter` instances from
        :class:`inspect.Parameter` instances.

        Parameter descriptions are a subset of those defined on
        :class:`~forge.FParameter`

        :param native: an instance of :class:`inspect.Parameter`, used as a
            template for creating a new :class:`~forge.FParameter`
            :returns: a new instance of :class:`~forge.FParameter`, using
            :paramref:`~forge.FParameter.from_native.native` as a template
        """
        return cls(
            kind=native.kind,
            name=native.name,
            interface_name=native.name,
            default=cls.empty.ccoerce_synthetic(native.default),
            type=cls.empty.ccoerce_synthetic(native.annotation),
        )

    @classmethod
    def create_positional_only(
        cls,
        name=None,
        interface_name=None,
        *,
        default=empty,
        factory=empty,
        type=empty,
        converter=None,
        validator=None,
        bound=False,
        metadata=None,
    ) -> 'FParameter':
        """
        A factory method for creating :term:`positional-only`
        :class:`~forge.FParameter` instances.

        :param name: see :paramref:`~forge.FParameter.name`
        :param interface_name: see :paramref:`~forge.FParameter.interface_name`
        :param default: see :paramref:`~forge.FParameter.default`
        :param factory: see :paramref:`~forge.FParameter.factory`
        :param type: see :paramref:`~forge.FParameter.type`
        :param converter: see :paramref:`~forge.FParameter.converter`
        :param validator: see :paramref:`~forge.FParameter.validator`
        :param bound: see :paramref:`~forge.FParameter.bound`
        :param metadata: see :paramref:`~forge.FParameter.metadata`
        """
        # pylint: disable=W0622, redefined-builtin
        return cls(
            kind=cls.POSITIONAL_ONLY,
            name=name,
            interface_name=interface_name,
            default=default,
            factory=factory,
            type=type,
            converter=converter,
            validator=validator,
            bound=bound,
            metadata=metadata,
        )

    @classmethod
    def create_positional_or_keyword(
        cls,
        name=None,
        interface_name=None,
        *,
        default=empty,
        factory=empty,
        type=empty,
        converter=None,
        validator=None,
        bound=False,
        metadata=None,
    ) -> 'FParameter':
        """
        A factory method for creating :term:`positional-or-keyword`
        :class:`~forge.FParameter` instances.

        :param name: see :paramref:`~forge.FParameter.name`
        :param interface_name: see :paramref:`~forge.FParameter.interface_name`
        :param default: see :paramref:`~forge.FParameter.default`
        :param factory: see :paramref:`~forge.FParameter.factory`
        :param type: see :paramref:`~forge.FParameter.type`
        :param converter: see :paramref:`~forge.FParameter.converter`
        :param validator: see :paramref:`~forge.FParameter.validator`
        :param bound: see :paramref:`~forge.FParameter.bound`
        :param metadata: see :paramref:`~forge.FParameter.metadata`
        """
        # pylint: disable=W0622, redefined-builtin
        return cls(
            kind=cls.POSITIONAL_OR_KEYWORD,
            name=name,
            interface_name=interface_name,
            default=default,
            factory=factory,
            type=type,
            converter=converter,
            validator=validator,
            bound=bound,
            metadata=metadata,
        )

    @classmethod
    def create_contextual(
        cls, name=None, interface_name=None, *, type=empty, metadata=None
    ) -> 'FParameter':
        """
        A factory method for creating :term:`positional-or-keyword`
        :class:`~forge.FParameter` instances that are ``contextual`` (this value
        is passed to other :class:`~forge.FParameter`s ``converter`` and
        ``validator`` functions.)

        :param name: see :paramref:`~forge.FParameter.name`
        :param interface_name: see :paramref:`~forge.FParameter.interface_name`
        :param type: see :paramref:`~forge.FParameter.type`
        :param metadata: see :paramref:`~forge.FParameter.metadata`
        """
        # pylint: disable=W0622, redefined-builtin
        return cls(
            kind=cls.POSITIONAL_OR_KEYWORD,
            name=name,
            interface_name=interface_name,
            type=type,
            contextual=True,
            metadata=metadata,
        )

    @classmethod
    def create_var_positional(
        cls, name, *, type=empty, converter=None, validator=None, metadata=None
    ) -> 'FParameter':
        """
        A factory method for creating :term:`var-positional`
        :class:`~forge.FParameter` instances.

        :param name: see :paramref:`~forge.FParameter.name`
        :param type: see :paramref:`~forge.FParameter.type`
        :param converter: see :paramref:`~forge.FParameter.converter`
        :param validator: see :paramref:`~forge.FParameter.validator`
        :param metadata: see :paramref:`~forge.FParameter.metadata`
        """
        # pylint: disable=W0622, redefined-builtin
        return cls(
            kind=cls.VAR_POSITIONAL,
            name=name,
            type=type,
            converter=converter,
            validator=validator,
            metadata=metadata,
        )

    @classmethod
    def create_keyword_only(
        cls,
        name=None,
        interface_name=None,
        *,
        default=empty,
        factory=empty,
        type=empty,
        converter=None,
        validator=None,
        bound=False,
        metadata=None,
    ) -> 'FParameter':
        """
        A factory method for creating :term:`keyword-only`
        :class:`~forge.FParameter` instances.

        :param name: see :paramref:`~forge.FParameter.name`
        :param interface_name: see :paramref:`~forge.FParameter.interface_name`
        :param default: see :paramref:`~forge.FParameter.default`
        :param factory: see :paramref:`~forge.FParameter.factory`
        :param type: see :paramref:`~forge.FParameter.type`
        :param converter: see :paramref:`~forge.FParameter.converter`
        :param validator: see :paramref:`~forge.FParameter.validator`
        :param bound: see :paramref:`~forge.FParameter.bound`
        :param metadata: see :paramref:`~forge.FParameter.metadata`
        """
        # pylint: disable=W0622, redefined-builtin
        return cls(
            kind=cls.KEYWORD_ONLY,
            name=name,
            interface_name=interface_name,
            default=default,
            factory=factory,
            type=type,
            converter=converter,
            validator=validator,
            bound=bound,
            metadata=metadata,
        )

    @classmethod
    def create_var_keyword(
        cls, name, *, type=empty, converter=None, validator=None, metadata=None
    ) -> 'FParameter':
        """
        A factory method for creating :term:`var-keyword`
        :class:`~forge.FParameter` instances.

        :param name: see :paramref:`~forge.FParameter.name`
        :param type: see :paramref:`~forge.FParameter.type`
        :param converter: see :paramref:`~forge.FParameter.converter`
        :param validator: see :paramref:`~forge.FParameter.validator`
        :param metadata: see :paramref:`~forge.FParameter.metadata`
        """
        # pylint: disable=W0622, redefined-builtin
        return cls(
            kind=cls.VAR_KEYWORD,
            name=name,
            type=type,
            converter=converter,
            validator=validator,
            metadata=metadata,
        )


# Convenience
_T_PARAM = typing.TypeVar('_T_PARAM', inspect.Parameter, FParameter)
_TYPE_FINDITER_PARAMETERS = typing.Iterable[_T_PARAM]
_TYPE_FINDITER_SELECTOR = typing.Union[
    str,
    typing.Iterable[str],
    typing.Callable[[_T_PARAM], bool],
]
pos = FParameter.create_positional_only
arg = pok = FParameter.create_positional_or_keyword
kwarg = kwo = FParameter.create_keyword_only
ctx = FParameter.create_contextual
vpo = FParameter.create_var_positional
vkw = FParameter.create_var_keyword
self_ = ctx('self')
cls_ = ctx('cls')


class VarPositional(collections.abc.Iterable):
    """
    A psuedo-sequence that unpacks as a :term:`var-positional`
    :class:`~forge.FParameter`.

    Can also be called with arguments to generate another instance.

    Typical usage::

        >>> import forge
        >>> fsig = forge.FSignature(*forge.args)
        >>> print(fsig)
        <FSignature (*args)>

        >>> import forge
        >>> fsig = forge.FSignature(*forge.args(name='vars'))
        >>> print(fsig)
        <FSignature (*vars)>

    While ``name`` can be supplied (by default it's ``args``),
    ``interface_name`` is unavailable.
    This is because when :class:`~forge.FSignature` maps parameters, the mapping
    between :term:`var-positional` parameters is 1:1, so the interface name for
    :term:`var-positional` is auto-discovered.

    Implements :class:`collections.abc.Iterable`, with provided: ``__iter__``.
    Inherits method: ``__next__``.

    :param name: see :paramref:`~forge.FParameter.name`
    :param type: see :paramref:`~forge.FParameter.type`
    :param converter: see :paramref:`~forge.FParameter.converter`
    :param validator: see :paramref:`~forge.FParameter.validator`
    :param metadata: see :paramref:`~forge.FParameter.metadata`
    """

    _default_name = 'args'

    def __init__(
        self,
        name: _TYPE_FP_NAME = None,
        *,
        type: _TYPE_FP_TYPE = empty,
        converter: _TYPE_FP_CONVERTER = None,
        validator: _TYPE_FP_VALIDATOR = None,
        metadata: typing.Optional[_TYPE_FP_METADATA] = None,
    ) -> None:
        # pylint: disable=W0622, redefined-builtin
        self.name = name or self._default_name
        self.type = type
        self.converter = converter
        self.validator = validator
        self.metadata = metadata

    @property
    def fparameter(self) -> 'FParameter':
        """
        :returns: a representation of this
            :class:`~forge._parameter.VarPositional` as a
            :class:`~forge.FParameter` of :term:`parameter kind`
            :term:`var-positional`, with attributes ``name``, ``converter``,
            ``validator`` and ``metadata`` from the instance.
        """
        # pylint: disable=E1101, no-member
        return FParameter.create_var_positional(
            name=self.name,
            type=self.type,
            converter=self.converter,
            validator=self.validator,
            metadata=self.metadata,
        )

    def __iter__(self) -> typing.Iterator:
        """
        Concrete method for :class:`collections.abc.Iterable`

        :returns: an iterable consisting of one item: the representation of this
            :class:`~forge._parameter.VarPositional` as a
            :class:`~forge.FParameter` via
            :attr:`~forge._parameter.VarPositional.fparameter`.
        """
        return iter((self.fparameter,))

    def __call__(
        self,
        name: _TYPE_FP_NAME = None,
        *,
        type: _TYPE_FP_TYPE = empty,
        converter: _TYPE_FP_CONVERTER = None,
        validator: _TYPE_FP_VALIDATOR = None,
        metadata: typing.Optional[_TYPE_FP_METADATA] = None,
    ) -> 'VarPositional':
        """
        A factory method which creates a new
        :class:`~forge._parameter.VarPositional` instance.
        Convenient for use like::

            *args(converter=lambda ctx, name, value: value[::-1])

        :param name: see :paramref:`~forge.FParameter.name`
        :param type: see :paramref:`~forge.FParameter.type`
        :param converter: see :paramref:`~forge.FParameter.converter`
        :param validator: see :paramref:`~forge.FParameter.validator`
        :param metadata: see :paramref:`~forge.FParameter.metadata`
        :returns: a new instance of :class:`~forge._parameter.VarPositional`
        """
        # pylint: disable=W0622, redefined-builtin
        return builtins.type(self)(
            name=name,
            type=type,
            converter=converter,
            validator=validator,
            metadata=metadata,
        )


class VarKeyword(collections.abc.Mapping):
    """
    A psuedo-collection that unpacks as a :term:`var-keyword`
    :class:`~forge.FParameter`.

    Can also be called with arguments to generate another instance.

    Typical usage::

        >>> import forge
        >>> fsig = forge.FSignature(**forge.kwargs)
        >>> print(fsig)
        <FSignature (**kwargs)>

        >>> import forge
        >>> fsig = forge.FSignature(**forge.kwargs(name='items'))
        >>> print(fsig)
        <FSignature (**items)>

    While ``name`` can be supplied (by default it's ``kwargs``),
    ``interface_name`` is unavailable.
    This is because when :class:`~forge.FSignature` maps parameters, the mapping
    between :term:`var-keyword` parameters is 1:1, so the interface name for
    :term:`var-keyword` is auto-discovered.

    Implements :class:`collections.abc.Mapping`, with provided: ``__getitem__``,
    ``__iter__`` and ``__len__``. Inherits methods: ``__contains__``, ``keys``,
    ``items``, ``values``, ``get``, ``__eq__`` and ``__ne__``.

    :param name: see :paramref:`~forge.FParameter.name`
    :param type: see :paramref:`~forge.FParameter.type`
    :param converter: see :paramref:`~forge.FParameter.converter`
    :param validator: see :paramref:`~forge.FParameter.validator`
    :param metadata: see :paramref:`~forge.FParameter.metadata`
    """

    _default_name = 'kwargs'

    def __init__(
        self,
        name: _TYPE_FP_NAME = None,
        *,
        type: _TYPE_FP_TYPE = empty,
        converter: _TYPE_FP_CONVERTER = None,
        validator: _TYPE_FP_VALIDATOR = None,
        metadata: typing.Optional[_TYPE_FP_METADATA] = None,
    ) -> None:
        # pylint: disable=W0622, redefined-builtin
        self.name = name or self._default_name
        self.type = type
        self.converter = converter
        self.validator = validator
        self.metadata = metadata

    @property
    def fparameter(self) -> 'FParameter':
        """
        :returns: a representation of this :class:`~forge._parameter.VarKeyword`
            as a :class:`~forge.FParameter` of :term:`parameter kind`
            :term:`var-keyword`, with attributes ``name``, ``converter``,
            ``validator`` and ``metadata`` from the instance.
        """
        # pylint: disable=E1101, no-member
        return FParameter.create_var_keyword(
            name=self.name,
            type=self.type,
            converter=self.converter,
            validator=self.validator,
            metadata=self.metadata,
        )

    def __getitem__(self, key: str) -> 'FParameter':
        """
        Concrete method for :class:`collections.abc.Mapping`

        :key: only retrieves for :paramref:`.VarKeyword.name`
        :raise: KeyError (if ``key`` is not
            :paramref:`~forge._parameter.VarKeyword.name`)
        :returns: a representation of this
            :class:`~forge._parameter.VarKeyword` as a
            :class:`~forge.FParameter` via
            :attr:`~forge._parameter.VarKeyword.fparameter`.
        """
        if self.name == key:
            return self.fparameter
        raise KeyError(key)

    def __iter__(self) -> typing.Iterator[str]:
        """
        Concrete method for :class:`collections.abc.Mapping`

        :returns: an iterable consisting of one item: the representation of this
            :class:`~forge._parameter.VarKeyword` as a
            :class:`~forge.FParameter` via
            :attr:`~forge._parameter.VarKeyword.fparameter`.
        """
        return iter({self.name: self.fparameter})

    def __len__(self) -> int:
        """
        Concrete method for :class:`collections.abc.Mapping`

        :returns: 1
        """
        return 1

    def __call__(
        self,
        name: _TYPE_FP_NAME = None,
        *,
        type: _TYPE_FP_TYPE = empty,
        converter: _TYPE_FP_CONVERTER = None,
        validator: _TYPE_FP_VALIDATOR = None,
        metadata: typing.Optional[_TYPE_FP_METADATA] = None,
    ) -> 'VarKeyword':
        """
        A factory method which creates a new
        :class:`~forge._parameter.VarKeyword` instance.
        Convenient for use like::

            **kwargs(
                converter=lambda ctx, name, value:
                    {'_' + k: v for k, v in value.items()},
            )

        :param name: see :paramref:`~forge.FParameter.name`
        :param type: see :paramref:`~forge.FParameter.type`
        :param converter: see :paramref:`~forge.FParameter.converter`
        :param validator: see :paramref:`~forge.FParameter.validator`
        :param metadata: see :paramref:`~forge.FParameter.metadata`
        :returns: a new instance of :class:`~forge._parameter.VarKeyword`
        """
        # pylint: disable=W0622, redefined-builtin
        return builtins.type(self)(
            name=name,
            type=type,
            converter=converter,
            validator=validator,
            metadata=metadata,
        )


# Convenience
args = VarPositional()
kwargs = VarKeyword()


def findparam(
    parameters: _TYPE_FINDITER_PARAMETERS, selector: _TYPE_FINDITER_SELECTOR
) -> typing.Iterator[_T_PARAM]:
    """
    Return an iterator yielding those parameters (of type
    :class:`inspect.Parameter` or :class:`~forge.FParameter`) that are
    mached by the selector.

    :paramref:`~forge.findparam.selector` is used differently based on what is
    supplied:

    - str: a parameter is found if its :attr:`name` attribute is contained
    - Iterable[str]: a parameter is found if its :attr:`name` attribute is
        contained
    - callable: a parameter is found if the callable (which receives the
        parameter), returns a truthy value.

    :param parameters: an iterable of :class:`inspect.Parameter` or
        :class:`~forge.FParameter`
    :param selector: an identifier which is used to determine whether a
        parameter matches.
    :returns: an iterator yield parameters
    """
    if isinstance(selector, str):
        return filter(lambda param: param.name == selector, parameters)
    elif isinstance(selector, typing.Iterable):
        selector = list(selector)
        return filter(
            lambda param: param.name in selector,
            parameters,
        )
    return filter(selector, parameters)  # else: callable(selector)


def get_context_parameter(parameters: typing.Iterable[FParameter]):
    """
    Get the first context parameter from the provided parameters.

    :param parameters: parameters to search for a ``contextual`` parameter
    :returns: the first :term:`var-keyword` parameter from
        :paramref:`get_var_keyword_parameters.parameters` if it exists,
        else ``None``.
    """
    try:
        return next(findparam(parameters, lambda p: p.contextual))
    except StopIteration:
        return None


def get_var_keyword_parameter(parameters: _TYPE_FINDITER_PARAMETERS):
    """
    Get the first :term:`var-keyword` :term:`parameter kind` from the provided
    parameters.

    :param parameters: parameters to search for :term:`var-keyword`
        :term:`parameter kind`.
    :returns: the first :term:`var-keyword` parameter from
        :paramref:`get_var_keyword_parameters.parameters` if it exists,
        else ``None``.
    """
    try:
        return next(findparam(parameters, lambda p: p.kind is VAR_KEYWORD))
    except StopIteration:
        return None


def get_var_positional_parameter(parameters: _TYPE_FINDITER_PARAMETERS):
    """
    Get the first :term:`var-positional` :term:`parameter kind` from the
    provided parameters.

    :param parameters: parameters to search for :term:`var-positional`
        :term:`parameter kind`.
    :returns: the first :term:`var-positional` parameter from
        :paramref:`get_var_positional_parameters.parameters` if it exists,
        else ``None``.
    """
    try:
        return next(findparam(parameters, lambda p: p.kind is VAR_POSITIONAL))
    except StopIteration:
        return None


class FSignature(Immutable, collections.abc.Sequence):
    """
    An immutable, validated representation of a signature composed of
    :class:`~forge.FParameter` instances, and a return type annotation.

    Sequence methods are supported and ``__getitem__`` is overloaded to provide
    access to parameters by index, name, or a slice.
    Described in further detail: :meth:`~forge.FSignature.__getitem__`

    :param parameters: an iterable of :class:`~forge.FParameter` that makes up
        the signature
    :param return_annotation: the return type annotation for the signature
    :param __validate_parameters__: whether the sequence of provided parameters
        should be validated
    """

    __slots__ = ('_data', 'return_annotation')

    def __init__(
        self,
        parameters: typing.Optional[typing.Iterable['FParameter']] = None,
        *,
        return_annotation: typing.Any = empty.native,
        __validate_parameters__: bool = False,
    ) -> None:
        super().__init__(
            _data=list(parameters or ()),
            return_annotation=return_annotation,
        )
        if __validate_parameters__:
            self.validate()

    def __len__(self):
        return len(self._data)

    @typing.overload
    def __getitem__(self, index: int) -> 'FParameter':
        pass  # pragma: no cover

    @typing.overload
    def __getitem__(self, index: slice) -> typing.List[FParameter]:
        # pylint: disable=E0102, function-redefined
        pass  # pragma: no cover

    @typing.overload
    def __getitem__(self, index: str) -> 'FParameter':
        # pylint: disable=E0102, function-redefined
        pass  # pragma: no cover

    def __getitem__(self, index):
        """
        Depending on the type of ``index`` (integer, string, or slice), this
        method returns :class:`~forge.FParameter <parameters>` using the
        following strategies:

        - ``index`` as ``str``: the first parameter (and if the signature is \
        validated, the *only* parameter) with ``index`` as a ``name`` is
        returned. \
        If no parameter is found, then a :class:`KeyError` is raised.

        - ``index`` as ``int``: the parameter at the ``index`` is returned. \
        If no parameter is found, then an :class:`IndexError` is raised.

        - ``index`` as a ``str`` slice: when accessing parameters using str \
        slice notation, e.g. ``fsignature['a':'c']``, all parameters \
        (beginning with the parameter with name 'a', and ending *inclusively* \
        with the parameter with name 'c', will be returned. \
        The ``step`` value of ``slice`` must not be provided.

        - ``index`` as an ``int`` slice: when accessing parameters using int \
        slice notation, e.g. ``fsignature[0:3]``, all parameters \
        (beginning with the parameter at index 0, and ending with the
        parameter before index 3, will be returned. \
        The ``step`` value of ``slice`` can be provided.

        :param index: a parameter index, name, or slice of indices or names
        :raises KeyError: if an instance of :class:`~forge.FParameter` with
            :paramref:`~forge.FParameter.name` doesn't exist on this
            :class:`~forge.FSignature`.
        :returns: the instance of :class:`~forge.FParameter.name` for which
            :paramref:`~forge.FSignature.__getitem__.index` corresponds.
        """
        # pylint: disable=E0102, function-redefined
        if isinstance(index, slice):
            typemap = {
                'start': type(index.start),
                'stop': type(index.stop),
                'step': type(index.step),
            }
            if {int, type(None)} >= set(typemap.values()):
                # slice with ints
                return self._data[index]

            if {str, type(None)} >= set(typemap.values()):
                # slice with strings
                if getattr(index, 'step', None):
                    raise TypeError('string slices cannot have a step')

                params = []
                visited_start = not bool(index.start)
                for param in self._data:
                    if param.name == index.start:
                        visited_start = True
                        params.append(param)
                    elif param.name == index.stop:
                        params.append(param)
                        break
                    elif visited_start:
                        params.append(param)
                return params

            raise TypeError('slice arguments must all be integers or all be strings')

        if isinstance(index, int):
            return self._data[index]

        if isinstance(index, str):
            for param in self._data:
                if param.name == index:
                    return param
            raise KeyError(index)

        raise TypeError(
            'indices must be integers, strings or slices, not {}'.format(
                getattr(type(index), '__name__', repr(index))
            )
        )

    def __str__(self) -> str:
        components = []
        if self:
            pos_param = next(
                findparam(self, lambda p: p.kind is POSITIONAL_ONLY),
                None,
            )
            has_positional = bool(pos_param)
            vpo_param = get_var_positional_parameter(self)
            has_var_positional = bool(vpo_param)

            for i, param in enumerate(self):
                last_ = self[i - 1] if (i > 0) else None
                next_ = self[i + 1] if (len(self) > i + 1) else None

                if (
                    not has_var_positional
                    and self[i].kind is KEYWORD_ONLY
                    and (not last_ or last_.kind is not KEYWORD_ONLY)
                ):
                    components.append('*')

                components.append(str(param))
                if (
                    has_positional
                    and self[i].kind is POSITIONAL_ONLY
                    and (not next_ or next_.kind is not POSITIONAL_ONLY)
                ):
                    components.append('/')

        ra_str = (
            ' -> {}'.format(inspect.formatannotation(self.return_annotation))
            if self.return_annotation is not empty.native
            else ''
        )

        return '({}){}'.format(', '.join(components), ra_str)

    def __repr__(self) -> str:
        return '<{} {}>'.format(type(self).__name__, self)

    @classmethod
    def from_native(cls, signature: inspect.Signature) -> 'FSignature':
        """
        A factory method that creates an instance of
        :class:`~forge.FSignature` from an instance of
        :class:`inspect.Signature`.
        Calls down to :class:`~forge.FParameter` to map the
        :attr:`inspect.Signature.parameters` to :class:`inspect.Parameter`
        instances.

        The ``return type`` annotation from the provided signature is not
        retained, as :meth:`~forge.FSignature.from_native` doesn't provide
        this functionality.

        :param signature: an instance of :class:`inspect.Signature` from which
            to derive the :class:`~forge.FSignature`
        :returns: an instance of :class:`~forge.FSignature` derived from the
            :paramref:`~forge.FSignature.from_native.signature` argument.
        """
        # pylint: disable=E1101, no-member
        return cls(
            [FParameter.from_native(native) for native in signature.parameters.values()],
            return_annotation=signature.return_annotation,
        )

    @classmethod
    def from_callable(cls, callable: typing.Callable) -> 'FSignature':
        """
        A factory method that creates an instance of
        :class:`~forge.FSignature` from a callable. Calls down to
        :meth:`~forge.FSignature.from_native` to do the heavy loading.

        :param callable: a callable from which to derive the
            :class:`~forge.FSignature`
        :returns: an instance of :class:`~forge.FSignature` derived from the
            :paramref:`~forge.FSignature.from_callable.callable` argument.
        """
        # pylint: disable=W0622, redefined-builtin
        return cls.from_native(inspect.signature(callable))

    @property
    def native(self) -> inspect.Signature:
        """
        Provides a representation of this :class:`~forge.FSignature` as an
        instance of :class:`inspect.Signature`
        """
        return inspect.Signature(
            [param.native for param in self if not param.bound],
            return_annotation=self.return_annotation,
        )

    def replace(
        self, *, parameters=void, return_annotation=void, __validate_parameters__=True
    ) -> 'FSignature':
        """
        Returns a copy of this :class:`~forge.FSignature` with replaced
        attributes.

        :param parameters: see :paramref:`~forge.FSignature.parameters`
        :param return_annotation: see
            :paramref:`~forge.FSignature.return_annotation`
        :param __validate_parameters__: see
            :paramref:`~forge.FSignature.__validate_parameters__`
        :returns: a new copy of :class:`~forge.FSignature` revised with
            replacements
        """
        return type(self)(
            parameters=parameters if parameters is not void else self._data,
            return_annotation=return_annotation
            if return_annotation is not void
            else self.return_annotation,
            __validate_parameters__=__validate_parameters__,
        )

    @property
    def parameters(self) -> types.MappingProxyType:
        """
        The signature's :class:`~forge.FParameter <parameters>`
        """
        return types.MappingProxyType(collections.OrderedDict([(p.name, p) for p in self._data]))

    def validate(self):
        """
        Validation ensures:

        - the appropriate order of parameters by kind:

            #. (optional) :term:`positional-only`, followed by
            #. (optional) :term:`positional-or-keyword`, followed by
            #. (optional) :term:`var-positional`, followed by
            #. (optional) :term:`keyword-only`, followed by
            #. (optional) :term:`var-keyword`

        - that non-default :term:`positional-only` or
            :term:`positional-or-keyword` parameters don't follow their
            respective similarly-kinded parameters with defaults,

            .. note::

                Python signatures allow non-default :term:`keyword-only`
                parameters to follow default :term:`keyword-only` parameters.

        - that at most there is one :term:`var-positional` parameter,

        - that at most there is one :term:`var-keyword` parameter,

        - that at most there is one ``context`` parameter, and that it
            is the first parameter (if it is provided.)

        - that no two instances of :class:`~forge.FParameter` share the same
            :paramref:`~forge.FParameter.name` or
            :paramref:`~forge.FParameter.interface_name`.
        """
        # pylint: disable=R0912, too-many-branches
        name_set = set()  # type: typing.Set[str]
        iname_set = set()  # type: typing.Set[str]
        for i, current in enumerate(self._data):
            if not isinstance(current, FParameter):
                raise TypeError("Received non-FParameter '{}'".format(current))
            elif not (current.name and current.interface_name):
                raise ValueError("Received unnamed parameter: '{}'".format(current))
            elif current.contextual:
                if i > 0:
                    raise TypeError('Only the first parameter can be contextual')

            if current.name in name_set:
                raise ValueError("Received multiple parameters with name '{}'".format(current.name))
            name_set.add(current.name)

            if current.interface_name in iname_set:
                raise ValueError(
                    "Received multiple parameters with interface_name '{}'".format(
                        current.interface_name
                    )
                )
            iname_set.add(current.interface_name)

            last = self._data[i - 1] if i > 0 else None
            if not last:
                continue

            elif current.kind < last.kind:
                raise SyntaxError(
                    "'{current}' of kind '{current.kind.name}' follows "
                    "'{last}' of kind '{last.kind.name}'".format(current=current, last=last)
                )
            elif current.kind is last.kind:
                if current.kind is FParameter.VAR_POSITIONAL:
                    raise TypeError('Received multiple variable-positional parameters')
                elif current.kind is FParameter.VAR_KEYWORD:
                    raise TypeError('Received multiple variable-keyword parameters')
                elif (
                    current.kind in (FParameter.POSITIONAL_ONLY, FParameter.POSITIONAL_OR_KEYWORD)
                    and last.default is not empty
                    and current.default is empty
                ):
                    raise SyntaxError('non-default parameter follows default parameter')


# Convenience
fsignature = FSignature.from_callable
self = self_
cls = cls_
