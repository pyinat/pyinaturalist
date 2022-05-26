"""
Shared unit test-related utilities.
Pytest will also automatically pick up any fixtures defined here.
"""
import json
import os
import re
from inspect import Parameter, getmembers, isfunction, signature
from os.path import join
from unittest.mock import MagicMock, patch

import pytest
from requests_cache import DO_NOT_CACHE, BaseCache

from pyinaturalist import enable_logging
from pyinaturalist.constants import SAMPLE_DATA_DIR
from pyinaturalist.session import ClientSession

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
        with patch('pyinaturalist.session.get_local_session', return_value=TestSession()), patch(
            'pyinaturalist.auth.get_local_session', return_value=TestSession()
        ), patch('pyinaturalist.client.ClientSession', TestSession):
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
    return join(SAMPLE_DATA_DIR, filename)


def load_sample_data(filename):
    with open(sample_data_path(filename), encoding='utf-8') as fh:
        if filename.endswith('json'):
            return json.load(fh)
        else:
            return fh.read()
