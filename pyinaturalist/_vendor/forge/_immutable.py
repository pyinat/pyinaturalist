import typing

from forge._exceptions import ImmutableInstanceError


def asdict(obj) -> typing.Dict:
    """
    Provides a "look" into any Python class instance by returning a dict
    into the attribute or slot values.

    :param obj: any Python class instance
    :returns: the attribute or slot values from :paramref:`.asdict.obj`
    """
    if hasattr(obj, '__dict__'):
        return {
            k: v for k, v in obj.__dict__.items()
            if not k.startswith('_')
        }

    return {
        k: getattr(obj, k) for k in obj.__slots__
        if not k.startswith('_')
    }


def replace(obj, **changes):
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
