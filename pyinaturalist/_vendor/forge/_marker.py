import inspect
import typing

# pylint: disable=C0103, invalid-name


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
