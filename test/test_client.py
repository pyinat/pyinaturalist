from unittest.mock import MagicMock, patch

import pytest
from requests import HTTPError, Response

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


@patch('pyinaturalist.client.get_access_token', return_value='token')
def test_client_auth__reuses_cached_token(get_access_token):
    client = iNatClient()
    final_params_1 = client.request(request_function, auth=True)
    final_params_2 = client.request(request_function, auth=True)

    assert final_params_1['access_token'] == 'token'
    assert final_params_2['access_token'] == 'token'
    get_access_token.assert_called_once()


@patch('pyinaturalist.client.get_access_token_via_auth_code', return_value='auth_code_token')
def test_client_auth_code_flow(get_access_token_via_auth_code):
    client = iNatClient(creds={'auth_flow': 'authorization_code', 'app_id': 'my_app_id'})
    final_params = client.request(request_function, auth=True)

    assert final_params['access_token'] == 'auth_code_token'
    get_access_token_via_auth_code.assert_called_once_with(app_id='my_app_id')


@patch(
    'pyinaturalist.client.get_access_token_via_auth_code',
    return_value='auth_code_token',
)
def test_client_auth_code_flow__reuses_cached_token(
    get_access_token_via_auth_code,
):
    client = iNatClient(creds={'auth_flow': 'authorization_code', 'app_id': 'my_app_id'})
    final_params_1 = client.request(request_function, auth=True)
    final_params_2 = client.request(request_function, auth=True)

    assert final_params_1['access_token'] == 'auth_code_token'
    assert final_params_2['access_token'] == 'auth_code_token'
    get_access_token_via_auth_code.assert_called_once_with(app_id='my_app_id')


@patch('pyinaturalist.client.get_access_token_via_auth_code')
def test_client_auth_code_flow__request_access_token_override(get_access_token_via_auth_code):
    client = iNatClient(creds={'auth_flow': 'authorization_code', 'app_id': 'my_app_id'})
    final_params = client.request(request_function, auth=True, access_token='provided_token')

    assert final_params['access_token'] == 'provided_token'
    get_access_token_via_auth_code.assert_not_called()


@patch('pyinaturalist.client.get_access_token_via_auth_code', return_value='auth_code_token')
def test_client_auth_code_flow__filters_unrelated_creds(get_access_token_via_auth_code):
    client = iNatClient(
        creds={
            'auth_flow': 'authorization_code',
            'app_id': 'my_app_id',
            'username': 'user',
            'password': 'pass',
            'some_other_key': 'value',
        }
    )
    final_params = client.request(request_function, auth=True)

    assert final_params['access_token'] == 'auth_code_token'
    get_access_token_via_auth_code.assert_called_once_with(app_id='my_app_id')


def make_http_error(status_code):
    response = Response()
    response.status_code = status_code
    error = HTTPError(f'HTTP {status_code}')
    error.response = response
    return error


@patch('pyinaturalist.client.get_access_token', side_effect=['expired_token', 'fresh_token'])
def test_client_auth__refreshes_cached_token_on_401(get_access_token):
    mock_request = MagicMock(side_effect=[make_http_error(401), {'ok': True}])
    client = iNatClient()

    result = client.request(mock_request, auth=True)

    assert result == {'ok': True}
    assert get_access_token.call_count == 2
    assert mock_request.call_args_list[0].kwargs['access_token'] == 'expired_token'
    assert mock_request.call_args_list[1].kwargs['access_token'] == 'fresh_token'


@patch('pyinaturalist.client.get_access_token_via_auth_code', side_effect=['expired', 'fresh'])
def test_client_auth_code_flow__refreshes_cached_token_on_401(get_access_token_via_auth_code):
    mock_request = MagicMock(side_effect=[make_http_error(401), {'ok': True}])
    client = iNatClient(creds={'auth_flow': 'authorization_code', 'app_id': 'my_app_id'})

    result = client.request(mock_request, auth=True)

    assert result == {'ok': True}
    assert get_access_token_via_auth_code.call_count == 2
    first_call_kwargs = get_access_token_via_auth_code.call_args_list[0].kwargs
    second_call_kwargs = get_access_token_via_auth_code.call_args_list[1].kwargs
    assert first_call_kwargs == {'app_id': 'my_app_id'}
    assert second_call_kwargs == {'app_id': 'my_app_id', 'refresh': True}


@patch('pyinaturalist.client.get_access_token')
def test_client_auth__does_not_refresh_provided_access_token(get_access_token):
    mock_request = MagicMock(side_effect=make_http_error(401))
    client = iNatClient()

    with pytest.raises(HTTPError):
        client.request(mock_request, auth=True, access_token='provided')

    get_access_token.assert_not_called()
    assert mock_request.call_count == 1
