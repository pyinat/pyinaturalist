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