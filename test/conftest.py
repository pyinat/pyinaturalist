"""
Shared unit test-related utilities.
Pytest will also automatically pick up any fixtures defined here.
"""

import base64
import json
import os
import re
import warnings
from contextlib import contextmanager
from inspect import Parameter, getmembers, isfunction, signature
from unittest.mock import MagicMock, patch

import pytest
from requests import HTTPError, Response
from requests_cache import DO_NOT_CACHE, BaseCache

from pyinaturalist import enable_logging
from pyinaturalist.client import ClientSession
from pyinaturalist.constants import SAMPLE_DATA_DIR

# If ipdb is installed, register it as the default debugger
try:
    import ipdb  # noqa: F401

    os.environ['PYTHONBREAKPOINT'] = 'ipdb.set_trace'
except ImportError:
    pass


HTTP_FUNC_PATTERN = re.compile(r'(get|put|post|delete)_.+')

MOCK_CREDS_ENV = {
    'INAT_USERNAME': 'valid_username',
    'INAT_PASSWORD': 'valid_password',
    'INAT_APP_ID': 'valid_app_id',
    'INAT_APP_SECRET': 'valid_app_secret',
}
MOCK_CREDS_OAUTH = {
    'username': 'valid_username',
    'password': 'valid_password',
    'client_id': 'valid_app_id',
    'client_secret': 'valid_app_secret',
}

# Enable logging for urllib and other external loggers
enable_logging('DEBUG')


class TestSession(ClientSession):
    """Session class to use for tests, which disables rate-limiting and caching"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.limiter = MagicMock()
        self.cache = BaseCache(expire_after=DO_NOT_CACHE)


@pytest.fixture(scope='function', autouse=True)
def patch_session(request):
    """Disable request caching and rate-limiting during tests"""
    if 'enable_client_session' in request.keywords:
        yield
    else:
        with (
            patch('pyinaturalist.client.session.get_local_session', return_value=TestSession()),
            patch('pyinaturalist.client.oauth.get_local_session', return_value=TestSession()),
            patch('pyinaturalist.client.client.ClientSession', TestSession),
        ):
            yield


def get_module_functions(module):
    """Get all functions belonging to a module (excluding imports)"""
    return {
        name: member
        for name, member in getmembers(module)
        if isfunction(member) and member.__module__ == module.__name__
    }


def get_module_http_functions(module):
    """Get all functions belonging to a module and prefixed with an HTTP method"""
    return {
        name: func
        for name, func in get_module_functions(module).items()
        if HTTP_FUNC_PATTERN.match(name.lower())
    }


def get_mock_args_for_signature(func):
    """Automagically get a list of mock objects corresponding to the required arguments
    in a function's signature. Using ``inspect.Signature``, 'Required' is defined by:
    1. positional and 2. no default
    """
    required_args = [
        p
        for p in signature(func).parameters.values()
        if p.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)
        and p.default is Parameter.empty
    ]
    return [MagicMock()] * len(required_args)


def sample_data_path(filename):
    return SAMPLE_DATA_DIR / filename


def load_sample_data(filename):
    with open(sample_data_path(filename), encoding='utf-8') as fh:
        if filename.endswith('json'):
            return json.load(fh)
        else:
            return fh.read()


@contextmanager
def ignore_deprecation():
    """Temporarily silence deprecation warnings"""
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', category=DeprecationWarning)
        yield


def make_jwt(payload: dict) -> str:
    """Build a minimal unsigned JWT string with the given payload."""
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b'=').decode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b'=').decode()
    return f'{header}.{body}.fakesig'


def make_http_error(status_code: int) -> HTTPError:
    """Build an HTTPError with a response of the given status code."""
    response = Response()
    response.status_code = status_code
    error = HTTPError(f'HTTP {status_code}')
    error.response = response
    return error
