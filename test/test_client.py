from unittest.mock import MagicMock, patch

import pytest

from pyinaturalist.client import iNatClient
from pyinaturalist.docs import document_common_args

mock_session_1 = MagicMock()
mock_session_2 = MagicMock()

SETTINGS_1 = {
    'dry_run': True,
    'session': mock_session_1,
}
SETTINGS_2 = {
    'dry_run': False,
    'session': mock_session_2,
}
PARTIAL_SETTINGS = {'dry_run': True}
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
