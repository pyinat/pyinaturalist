from functools import wraps


class BaseController:
    """Base class for controllers. A controller provides an interface for all requests related to a
    single resource type. This is mainly for the purpose of splitting up :py:class:`.iNatClient`
    methods by resource type, which keeps code, documentation, and usage more organized and easier
    to navigate.
    """

    def __init__(self, client):
        self.client = client


def authenticated(func):
    """Decorator that will add an authentication token to request params, unless one has already
    been manually provided. This requires credentials to be provided either via :yp:class:`.iNatClient`
    arguments, environment variables, or keyring.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not kwargs.get('access_token'):
            kwargs['access_token'] = self.client.access_token
        return func(self, *args, **kwargs)

    return wrapper
