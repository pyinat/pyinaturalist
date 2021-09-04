from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from urllib3.util import Retry

from pyinaturalist.client import iNatClient
from pyinaturalist.constants import MAX_RETRIES, TOKEN_EXPIRATION
from pyinaturalist.docs import document_common_args

mock_session_1 = MagicMock()
mock_session_2 = MagicMock()

SETTINGS_1 = {
    'dry_run': True,
    'session': mock_session_1,
    'user_agent': 'pytest',
}
SETTINGS_2 = {
    'dry_run': False,
    'session': mock_session_2,
    'user_agent': 'python/requests',
}
PARTIAL_SETTINGS = {'dry_run': True, 'user_agent': 'pytest'}
PARAMS_1 = {'id': 1, 'name': 'test_1'}
PARAMS_2 = {'id': 2, 'name': 'test_2'}


@document_common_args
def request_function(id=None, name=None, **params):
    params['id'] = id
    params['name'] = name
    return params


@pytest.mark.parametrize(
    'client_settings, request_params, expected_params',
    [
        ({}, {}, {}),
        (SETTINGS_1, {}, SETTINGS_1),
        (PARTIAL_SETTINGS, {}, PARTIAL_SETTINGS),
        (SETTINGS_1, SETTINGS_2, SETTINGS_2),
        ({'default_params': PARAMS_1}, {}, PARAMS_1),
        ({'default_params': PARAMS_1}, PARAMS_2, PARAMS_2),
        ({'default_params': {'invalid_param': 'value'}}, {}, {}),
    ],
)
def test_client_settings(client_settings, request_params, expected_params):
    """Client settings should be applied as defaults, and not override explicit kw arguments"""
    client = iNatClient(**client_settings)
    final_params = client.request(request_function, **request_params)

    for k, v in expected_params.items():
        assert final_params[k] == v


@patch('pyinaturalist.client.get_access_token', return_value='token')
def test_client_auth(get_access_token):
    """An access token should be added to authenticated requests"""
    client = iNatClient()
    final_params_1 = client.request(request_function, auth=True)
    final_params_2 = client.request(request_function)

    assert final_params_1['access_token'] == 'token'
    assert 'access_token' not in final_params_2
    get_access_token.assert_called_once()


@patch('pyinaturalist.client.get_access_token', side_effect=['token_1', 'token_2'])
def test_client_auth_refresh(get_access_token):
    """An access token should be added to authenticated requests"""
    client = iNatClient()

    # Get an initial access token
    assert client.access_token == 'token_1'
    assert isinstance(client._token_expires, datetime)
    assert client._is_expired() is False

    # Wait for it to expire
    client._token_expires = datetime.utcnow() - TOKEN_EXPIRATION
    assert client._is_expired() is True

    # Expect a new access token
    assert client.access_token == 'token_2'
    assert client._is_expired() is False


def test_client_retry():
    """Custom retry settings should be mounted on the client's session and be retrievable via property"""
    client_1 = iNatClient()
    assert client_1.retry.total == MAX_RETRIES

    client_1.retry = Retry(total=2)
    client_2 = iNatClient(retry=Retry(total=2))
    assert client_1.retry.total == client_2.retry.total == 2
