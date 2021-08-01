from functools import wraps


class BaseController:
    """Base class for resource-specific controllers"""

    def __init__(self, client):
        self.client = client


def authenticated(func):
    """Decorator that will add an authentication token to request params, unless one has already
    been manually provided. Note that this requires credentials to be provided either via client
    settings, environment variables, or keyring.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not kwargs.get('access_token'):
            kwargs['access_token'] = self.client.access_token
        return func(self, *args, **kwargs)

    return wrapper
