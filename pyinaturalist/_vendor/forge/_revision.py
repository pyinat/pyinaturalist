import asyncio
import functools
import inspect
import types
import typing

import forge._immutable as immutable
from forge._marker import _void, empty
from forge._signature import (
    _TYPE_FINDITER_SELECTOR,
    FParameter,
    FSignature,
    fsignature,
    findparam,
    _get_pk_string,
    get_context_parameter,
    get_var_keyword_parameter,
    get_var_positional_parameter,
)
from forge._utils import CallArguments


class Mapper(immutable.Immutable):
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
            fsignature: FSignature,
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

    def __call__(
            self,
            *args: typing.Any,
            **kwargs: typing.Any
        ) -> CallArguments:
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
        except TypeError as exc:
            raise TypeError(
                '{callable_name}() {message}'.\
                format(
                    callable_name=self.callable.__name__,
                    message=exc.args[0],
                ),
            )
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
                    private_ba.arguments[to_name]\
                        [from_param.interface_name] = to_val
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
        return arguments[self.context_param.name] \
            if self.context_param \
            else None

    @staticmethod
    def map_parameters(
            from_: FSignature,
            to_: inspect.Signature,
        ) -> types.MappingProxyType:
        '''
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
        '''
        # pylint: disable=W0622, redefined-builtin
        from_vpo_param = get_var_positional_parameter(from_)
        from_vkw_param = get_var_keyword_parameter(from_)
        from_param_index = {
            fparam.interface_name: fparam for fparam in from_
            if fparam not in (from_vpo_param, from_vkw_param)
        }

        to_vpo_param = \
            get_var_positional_parameter(to_.parameters.values())
        to_vkw_param = \
            get_var_keyword_parameter(to_.parameters.values())
        to_param_index = {
            param.name: param for param in to_.parameters.values()
            if param not in (to_vpo_param, to_vkw_param)
        }

        mapping = {}
        for name in list(to_param_index):
            param = to_param_index.pop(name)
            try:
                param_t = from_param_index.pop(name)
            except KeyError:
                # masked mapping, e.g. f() -> g(a=1)
                if param.default is not empty.native:
                    continue

                # invalid mapping, e.g. f() -> g(a)
                kind_repr = _get_pk_string(param.kind)
                raise TypeError(
                    "Missing requisite mapping to non-default {kind_repr} "
                    "parameter '{pri_name}'".\
                    format(kind_repr=kind_repr, pri_name=name)
                )
            else:
                mapping[param_t.name] = name

        if from_vpo_param:
            # invalid mapping, e.g. f(*args) -> g()
            if not to_vpo_param:
                kind_repr = _get_pk_string(FParameter.VAR_POSITIONAL)
                raise TypeError(
                    "Missing requisite mapping from {kind_repr} parameter "
                    "'{from_vpo_param.name}'".\
                    format(kind_repr=kind_repr, from_vpo_param=from_vpo_param)
                )
            # var-positional mapping, e.g. f(*args) -> g(*args)
            mapping[from_vpo_param.name] = to_vpo_param.name

        if from_vkw_param:
            # invalid mapping, e.g. f(**kwargs) -> g()
            if not to_vkw_param:
                kind_repr = _get_pk_string(FParameter.VAR_KEYWORD)
                raise TypeError(
                    "Missing requisite mapping from {kind_repr} parameter "
                    "'{from_vkw_param.name}'".\
                    format(kind_repr=kind_repr, from_vkw_param=from_vkw_param)
                )
            # var-keyword mapping, e.g. f(**kwargs) -> g(**kwargs)
            mapping[from_vkw_param.name] = to_vkw_param.name

        if from_param_index:
            # invalid mapping, e.g. f(a) -> g()
            if not to_vkw_param:
                raise TypeError(
                    "Missing requisite mapping from parameters ({})".format(
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
            self,
            callable: typing.Callable[..., typing.Any]
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
            next_ = self.revise(callable.__mapper__.fsignature)  # type: ignore
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
            @functools.wraps(callable)  # type: ignore
            def inner(*args, **kwargs):
                # pylint: disable=E1102, not-callable
                mapped = inner.__mapper__(*args, **kwargs)
                return callable(*mapped.args, **mapped.kwargs)

        next_.validate()
        inner.__mapper__ = Mapper(next_, callable)  # type: ignore
        inner.__signature__ = inner.__mapper__.public_signature  # type: ignore
        return inner

    def revise(self, previous: FSignature) -> FSignature:
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

    def revise(self, previous: FSignature) -> FSignature:
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
            include: typing.Optional[_TYPE_FINDITER_SELECTOR] = None,
            exclude: typing.Optional[_TYPE_FINDITER_SELECTOR] = None
        ) -> None:
        # pylint: disable=W0622, redefined-builtin
        if include is not None and exclude is not None:
            raise TypeError(
                "expected 'include', 'exclude', or neither, but received both"
            )

        self.signature = fsignature(callable)
        self.include = include
        self.exclude = exclude

    def revise(self, previous: FSignature) -> FSignature:
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
            return self.signature.replace(parameters=list(
                findparam(self.signature, self.include)
            ))
        elif self.exclude:
            excluded = list(findparam(self.signature, self.exclude))
            return self.signature.replace(parameters=[
                param for param in self.signature if param not in excluded
            ])
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
    def __init__(
            self,
            callable: typing.Callable[[FSignature], FSignature]
        ) -> None:
        # pylint: disable=W0622, redefined-builtin
        self.callable = callable

    def revise(self, previous: FSignature) -> FSignature:
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


class returns(Revision): # pylint: disable=invalid-name
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
            self,
            callable: typing.Callable[..., typing.Any]
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
            sig = callable.__signature__  # type: ignore
            callable.__signature__ = sig.replace(  # type: ignore
                return_annotation=self.return_annotation
            )

        else:
            callable.__annotations__['return'] = self.return_annotation

        return callable

    def revise(self, previous: FSignature) -> FSignature:
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
                ) for name, param in sorted(
                    named_parameters.items(),
                    key=lambda i: i[1]._creation_order,
                )
            ]
        ]

    def revise(self, previous: FSignature) -> FSignature:
        """
        Produces a signature with the parameters provided at initialization.

        No validation is performed on the updated :class:`~forge.FSignature`,
        allowing it to be used as an intermediate revision in the context of
        :class:`~forge.compose`.

        :param previous: the :class:`~forge.FSignature` to modify
        :returns: a modified instance of :class:`~forge.FSignature`
        """
        return previous.replace(  # type: ignore
            parameters=self.parameters,
            __validate_parameters__=False,
        )

# Convenience name
sign = synthesize  # pylint: disable=C0103, invalid-name


class sort(Revision): # pylint: disable=C0103, invalid-name
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
            self,
            sortkey: typing.Optional[
                typing.Callable[[FParameter], typing.Any]
            ]=None
        ) -> None:
        self.sortkey = sortkey or self._sortkey

    def revise(self, previous: FSignature) -> FSignature:
        """
        Applies the sorting :paramref:`~forge.returns.return_annotation`, to
        the input signature.

        No validation is performed on the updated :class:`~forge.FSignature`,
        allowing it to be used as an intermediate revision in the context of
        :class:`~forge.compose`.

        :param previous: the :class:`~forge.FSignature` to modify
        :returns: a modified instance of :class:`~forge.FSignature`
        """
        return previous.replace(  # type: ignore
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
            self,
            selector: _TYPE_FINDITER_SELECTOR,
            multiple: bool = False,
            raising: bool = True
        ) -> None:
        self.selector = selector
        self.multiple = multiple
        self.raising = raising

    def revise(self, previous: FSignature) -> FSignature:
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
                raise ValueError(
                    "No parameter matched selector '{}'".format(self.selector)
                )
            return previous

        if not self.multiple:
            del excluded[1:]

        # https://github.com/python/mypy/issues/5156
        return previous.replace(  # type: ignore
            parameters=[
                param for param in previous
                if param not in excluded
            ],
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
            insertion: typing.Union[FParameter, typing.Iterable[FParameter]],
            *,
            index: int = None,
            before: _TYPE_FINDITER_SELECTOR = None,
            after: _TYPE_FINDITER_SELECTOR = None
        ) -> None:
        provided = dict(filter(
            lambda i: i[1] is not None,
            {'index': index, 'before': before, 'after': after}.items(),
        ))
        if not provided:
            raise TypeError(
                "expected keyword argument 'index', 'before', or 'after'"
            )
        elif len(provided) > 1:
            raise TypeError(
                "expected 'index', 'before' or 'after' received multiple"
            )

        self.insertion = [insertion] \
            if isinstance(insertion, FParameter) \
            else list(insertion)
        self.index = index
        self.before = before
        self.after = after

    def revise(self, previous: FSignature) -> FSignature:
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
            except StopIteration:
                raise ValueError(
                    "No parameter matched selector '{}'".format(self.before)
                )

            for param in pparams:
                if param is match:
                    nparams.extend(self.insertion)
                nparams.append(param)
        elif self.after:
            try:
                match = next(findparam(pparams, self.after))
            except StopIteration:
                raise ValueError(
                    "No parameter matched selector '{}'".format(self.after)
                )

            for param in previous:
                nparams.append(param)
                if param is match:
                    nparams.extend(self.insertion)
        else:
            nparams = pparams[:self.index] + \
                self.insertion + \
                pparams[self.index:]

        # https://github.com/python/mypy/issues/5156
        return previous.replace(  # type: ignore
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
            selector: _TYPE_FINDITER_SELECTOR,
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
            metadata=_void
        ) -> None:
        # pylint: disable=W0622, redefined-builtin
        # pylint: disable=R0914, too-many-locals
        self.selector = selector
        self.multiple = multiple
        self.raising = raising
        self.updates = {
            k: v for k, v in {
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
            }.items() if v is not _void
        }

    def revise(self, previous: FSignature) -> FSignature:
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
                raise ValueError(
                    "No parameter matched selector '{}'".format(self.selector)
                )
            return previous

        if not self.multiple:
            del matched[1:]

        # https://github.com/python/mypy/issues/5156
        return previous.replace(  # type: ignore
            parameters=[
                param.replace(**self.updates) if param in matched else param
                for param in previous
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
    def __init__(
            self,
            selector: _TYPE_FINDITER_SELECTOR,
            parameter: FParameter
        ) -> None:
        self.selector = selector
        self.parameter = parameter

    def revise(self, previous: FSignature) -> FSignature:
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
        except StopIteration:
            raise ValueError(
                "No parameter matched selector '{}'".format(self.selector)
            )

        # https://github.com/python/mypy/issues/5156
        return previous.replace(  # type: ignore
            parameters=[
                self.parameter if param is match else param
                for param in previous
            ],
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
        provided = dict(filter(
            lambda i: i[1] is not None,
            {'index': index, 'before': before, 'after': after}.items(),
        ))
        if not provided:
            raise TypeError(
                "expected keyword argument 'index', 'before', or 'after'"
            )
        elif len(provided) > 1:
            raise TypeError(
                "expected 'index', 'before' or 'after' received multiple"
            )

        self.selector = selector
        self.index = index
        self.before = before
        self.after = after

    def revise(self, previous: FSignature) -> FSignature:
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
        except StopIteration:
            raise ValueError(
                "No parameter matched selector '{}'".format(self.selector)
            )

        if self.before:
            try:
                before = next(findparam(previous, self.before))
            except StopIteration:
                raise ValueError(
                    "No parameter matched selector '{}'".format(self.before)
                )

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
            except StopIteration:
                raise ValueError(
                    "No parameter matched selector '{}'".format(self.after)
                )

            parameters = []
            for param in previous:
                if param is not selected:
                    parameters.append(param)
                if param is after:
                    parameters.append(selected)
        else:
            parameters = [
                param for param in previous
                if param is not selected
            ]
            parameters.insert(self.index, selected)

        # https://github.com/python/mypy/issues/5156
        return previous.replace(  # type: ignore
            parameters=parameters,
            __validate_parameters__=False,
        )


# Convenience name
move = translocate  # pylint: disable=C0103, invalid-name
