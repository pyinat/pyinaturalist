import base64
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from requests import HTTPError, Response

from pyinaturalist.client import iNatClient
from pyinaturalist.docs import document_common_args
from pyinaturalist.exceptions import AuthenticationError

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


# Item 2: auth_flow validation
# ----------------------------


@pytest.mark.parametrize('bad_flow', ['oauth2', 'client_credentials', '', 'Authorization_Code'])
def test_client_auth__invalid_flow_raises(bad_flow):
    """iNatClient raises AuthenticationError at init for an unrecognized auth_flow."""
    with pytest.raises(AuthenticationError, match='Unsupported auth_flow'):
        iNatClient(creds={'auth_flow': bad_flow})


@pytest.mark.parametrize('good_flow', ['password', 'authorization_code'])
def test_client_auth__valid_flows_accepted(good_flow):
    """iNatClient accepts all supported auth_flow values without raising."""
    client = iNatClient(creds={'auth_flow': good_flow})
    assert client.creds['auth_flow'] == good_flow


# Item 8: _TokenInfo lifecycle
# ----------------------------


def _make_jwt(payload: dict) -> str:
    """Build a minimal unsigned JWT string with the given payload."""
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b'=').decode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b'=').decode()
    return f'{header}.{body}.fakesig'


@patch('pyinaturalist.client.get_access_token', return_value='plain_token')
def test_client_auth__token_info_populated(get_access_token):
    """After an authenticated request, _token_info is populated with correct metadata."""
    before = datetime.now(tz=timezone.utc)
    client = iNatClient()
    client.request(request_function, auth=True)

    info = client._token_info
    assert info is not None
    assert info.token == 'plain_token'
    assert info.flow == 'password'
    assert info.obtained_at >= before
    assert info.obtained_at.tzinfo == timezone.utc


@patch('pyinaturalist.client.get_access_token_via_auth_code', return_value='ac_token')
def test_client_auth__token_info_flow_auth_code(get_access_token_via_auth_code):
    """flow is set to 'authorization_code' when using the auth code flow."""
    client = iNatClient(creds={'auth_flow': 'authorization_code', 'app_id': 'my_app'})
    client.request(request_function, auth=True)

    assert client._token_info is not None
    assert client._token_info.flow == 'authorization_code'


@patch('pyinaturalist.client.get_access_token')
def test_client_auth__token_info_exp_decoded(get_access_token):
    """expires_at is decoded from a JWT exp claim."""
    exp_ts = 1893456000
    jwt_token = _make_jwt({'exp': exp_ts})
    get_access_token.return_value = jwt_token

    client = iNatClient()
    client.request(request_function, auth=True)

    info = client._token_info
    assert info is not None
    assert info.expires_at is not None
    assert info.expires_at.tzinfo == timezone.utc
    assert int(info.expires_at.timestamp()) == exp_ts


@patch('pyinaturalist.client.get_access_token', return_value='plain_oauth_token')
def test_client_auth__token_info_no_exp_for_plain_token(get_access_token):
    """expires_at is None for a plain OAuth token that is not a JWT."""
    client = iNatClient()
    client.request(request_function, auth=True)

    assert client._token_info is not None
    assert client._token_info.expires_at is None


@patch('pyinaturalist.client.get_access_token', side_effect=['expired_token', 'fresh_token'])
def test_client_auth__token_info_updated_on_401(get_access_token):
    """_token_info is replaced (not stale) after a 401 triggers a refresh."""
    mock_request = MagicMock(side_effect=[make_http_error(401), {'ok': True}])
    client = iNatClient()

    client.request(mock_request, auth=True)

    assert client._token_info is not None
    assert client._token_info.token == 'fresh_token'
