import json
import os
from datetime import timezone
from unittest.mock import patch

import pytest
from keyring.errors import KeyringError
from requests import HTTPError, Response

from pyinaturalist.auth import (
    _decode_jwt_exp,
    get_access_token,
    get_access_token_via_auth_code,
    get_keyring_credentials,
    set_keyring_credentials,
    validate_token,
)
from pyinaturalist.constants import API_V0, KEYRING_KEY
from pyinaturalist.exceptions import AuthenticationError
from pyinaturalist.oauth_callback import CallbackResult
from pyinaturalist.session import ClientSession
from test.conftest import MOCK_CREDS_ENV, MOCK_CREDS_OAUTH, load_sample_data, make_jwt

token_accepted_json = load_sample_data('get_access_token.json')
token_rejected_json = load_sample_data('get_access_token_401.json')
jwt_json = load_sample_data('get_jwt.json')


OAUTH_ACCESS_TOKEN = '604e5df329b98eecd22bb0a84f88b68'
JWT_API_TOKEN = 'eyJ1c2VyX2lkIjoyMTE1MDUxLCJvYXV0aF9hcHBsaWNhdGlvbl9pZCI6NjQzLCJx'
JWT_RESPONSE_200 = Response()
JWT_RESPONSE_200.status_code = 200
JWT_RESPONSE_200._content = json.dumps(jwt_json).encode()
NOT_CACHED_RESPONSE = Response()
NOT_CACHED_RESPONSE.status_code = 504


# get_access_token
# --------------------


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', side_effect=[NOT_CACHED_RESPONSE, JWT_RESPONSE_200])
@pytest.mark.parametrize(
    'jwt, expected_token', [(False, OAUTH_ACCESS_TOKEN), (True, JWT_API_TOKEN)]
)
def test_get_access_token__token_type(mock_get_jwt, requests_mock, jwt, expected_token):
    requests_mock.post(f'{API_V0}/oauth/token', json=token_accepted_json, status_code=200)

    token = get_access_token(
        'valid_username', 'valid_password', 'valid_app_id', 'valid_app_secret', jwt=jwt
    )
    assert token == expected_token


@patch.dict(os.environ, {}, clear=True)
def test_get_access_token__cached_jwt(requests_mock):
    """An initial request will return a 200 if a JWT is already cached, or a 504 otherwise."""
    requests_mock.post(f'{API_V0}/oauth/token', json=token_accepted_json, status_code=200)
    requests_mock.get(f'{API_V0}/users/api_token', json=jwt_json, status_code=200)

    token_1 = get_access_token(
        'valid_username', 'valid_password', 'valid_app_id', 'valid_app_secret'
    )
    token_2 = get_access_token(
        'valid_username', 'valid_password', 'valid_app_id', 'valid_app_secret'
    )
    assert token_1 == token_2 == JWT_API_TOKEN


@patch.dict(os.environ, MOCK_CREDS_ENV)
@patch('pyinaturalist.auth.get_keyring_credentials')
@patch('pyinaturalist.auth._get_jwt', side_effect=[NOT_CACHED_RESPONSE, JWT_RESPONSE_200])
def test_get_access_token__envars(mock_get_jwt, mock_keyring_credentials, requests_mock):
    requests_mock.post(f'{API_V0}/oauth/token', json=token_accepted_json, status_code=200)

    token = get_access_token()
    assert token == JWT_API_TOKEN
    mock_keyring_credentials.assert_not_called()


@patch.dict(os.environ, {'INAT_USERNAME': 'valid_username', 'INAT_PASSWORD': 'valid_password'})
@patch('pyinaturalist.auth._get_jwt', side_effect=[NOT_CACHED_RESPONSE, JWT_RESPONSE_200])
def test_get_access_token__mixed_args_and_envars(mock_get_jwt, requests_mock):
    requests_mock.post(f'{API_V0}/oauth/token', json=token_accepted_json, status_code=200)

    token = get_access_token(app_id='valid_app_id', app_secret='valid_app_secret')
    assert token == JWT_API_TOKEN


@pytest.mark.enable_client_session
@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth.get_keyring_credentials', return_value=MOCK_CREDS_OAUTH)
@patch('pyinaturalist.auth._get_jwt', side_effect=[NOT_CACHED_RESPONSE, JWT_RESPONSE_200])
@patch.object(ClientSession, 'post')
def test_get_access_token__keyring(
    mock_post, mock_get_jwt, mock_keyring_credentials, requests_mock
):
    mock_post.return_value = Response()
    mock_post.return_value.status_code = 200
    mock_post.return_value._content = json.dumps(token_accepted_json).encode()

    get_access_token()
    submitted_json = mock_post.call_args[1]['json']
    assert submitted_json == {'grant_type': 'password', **MOCK_CREDS_OAUTH}
    mock_keyring_credentials.assert_called_once()


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth.get_keyring_credentials')
@patch('pyinaturalist.auth._get_jwt', return_value=NOT_CACHED_RESPONSE)
def test_get_access_token__missing_creds(mock_get_jwt, mock_keyring_credentials):
    with pytest.raises(AuthenticationError, match='Not all authentication parameters'):
        get_access_token('username')


@patch('pyinaturalist.auth._get_jwt', return_value=NOT_CACHED_RESPONSE)
def test_get_access_token__invalid_creds(mock_get_jwt, requests_mock):
    requests_mock.post(f'{API_V0}/oauth/token', json=token_rejected_json, status_code=401)

    with pytest.raises(HTTPError):
        get_access_token('username', 'password', 'app_id', 'app_secret')


# get_access_token_via_auth_code
# -----------------------------------


def _make_server_result(auth_code=None, auth_error=None):
    """Helper to build a CallbackResult for mocking get_auth_code_via_server."""
    return CallbackResult(auth_code=auth_code, auth_error=auth_error)


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', side_effect=[NOT_CACHED_RESPONSE, JWT_RESPONSE_200])
@patch(
    'pyinaturalist.oauth_callback.get_auth_code_via_server',
    return_value=_make_server_result('mock_auth_code'),
)
def test_get_access_token_via_auth_code__pkce(mock_server, mock_get_jwt, requests_mock):
    requests_mock.post(f'{API_V0}/oauth/token', json=token_accepted_json, status_code=200)

    token = get_access_token_via_auth_code(app_id='valid_app_id')
    assert token == JWT_API_TOKEN

    # Verify the token exchange payload includes PKCE fields
    submitted_json = requests_mock.last_request.json()
    assert submitted_json['grant_type'] == 'authorization_code'
    assert submitted_json['client_id'] == 'valid_app_id'
    assert submitted_json['code'] == 'mock_auth_code'
    assert 'code_verifier' in submitted_json
    assert 'client_secret' not in submitted_json


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', side_effect=[NOT_CACHED_RESPONSE, JWT_RESPONSE_200])
@patch(
    'pyinaturalist.oauth_callback.get_auth_code_via_server',
    return_value=_make_server_result('mock_auth_code'),
)
def test_get_access_token_via_auth_code__no_pkce(mock_server, mock_get_jwt, requests_mock):
    requests_mock.post(f'{API_V0}/oauth/token', json=token_accepted_json, status_code=200)

    token = get_access_token_via_auth_code(
        app_id='valid_app_id', app_secret='valid_app_secret', use_pkce=False
    )
    assert token == JWT_API_TOKEN

    # Verify the token exchange payload includes client_secret, not PKCE
    submitted_json = requests_mock.last_request.json()
    assert submitted_json['client_secret'] == 'valid_app_secret'
    assert 'code_verifier' not in submitted_json


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', side_effect=[NOT_CACHED_RESPONSE, JWT_RESPONSE_200])
@patch('pyinaturalist.oauth_callback.webbrowser.open')
@patch('builtins.input', return_value='oob_auth_code')
def test_get_access_token_via_auth_code__oob(mock_input, mock_browser, mock_get_jwt, requests_mock):
    requests_mock.post(f'{API_V0}/oauth/token', json=token_accepted_json, status_code=200)

    token = get_access_token_via_auth_code(app_id='valid_app_id', use_oob=True)
    assert token == JWT_API_TOKEN
    mock_input.assert_called_once()
    mock_browser.assert_called_once()

    # Verify the redirect_uri is OOB
    submitted_json = requests_mock.last_request.json()
    assert submitted_json['redirect_uri'] == 'urn:ietf:wg:oauth:2.0:oob'
    assert submitted_json['code'] == 'oob_auth_code'


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', return_value=NOT_CACHED_RESPONSE)
@patch(
    'pyinaturalist.oauth_callback.get_auth_code_via_server',
    return_value=_make_server_result('mock_auth_code'),
)
def test_get_access_token_via_auth_code__oauth(mock_server, mock_get_jwt, requests_mock):
    """jwt=False returns the raw OAuth access token, not a JWT."""
    requests_mock.post(f'{API_V0}/oauth/token', json=token_accepted_json, status_code=200)

    token = get_access_token_via_auth_code(app_id='valid_app_id', jwt=False)
    assert token == OAUTH_ACCESS_TOKEN
    # Only one _get_jwt call (the cache probe); no second call to fetch a JWT
    mock_get_jwt.assert_called_once()


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', return_value=JWT_RESPONSE_200)
def test_get_access_token_via_auth_code__cached_jwt(mock_get_jwt):
    """If a JWT is already cached, return it without starting the browser flow."""
    token = get_access_token_via_auth_code(app_id='valid_app_id')
    assert token == JWT_API_TOKEN


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', return_value=NOT_CACHED_RESPONSE)
@patch('pyinaturalist.oauth_callback.get_auth_code_via_server', return_value=_make_server_result())
def test_get_access_token_via_auth_code__timeout(mock_server, mock_get_jwt):
    with pytest.raises(AuthenticationError, match='No authorization code received'):
        get_access_token_via_auth_code(app_id='valid_app_id')


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', return_value=NOT_CACHED_RESPONSE)
@pytest.mark.parametrize(
    'kwargs, match',
    [
        ({}, 'app_id is required'),
        ({'app_id': 'valid_app_id', 'use_pkce': False}, 'app_secret is required'),
    ],
)
def test_get_access_token_via_auth_code__missing_creds(mock_get_jwt, kwargs, match):
    with pytest.raises(AuthenticationError, match=match):
        get_access_token_via_auth_code(**kwargs)


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', side_effect=[NOT_CACHED_RESPONSE, JWT_RESPONSE_200])
@patch(
    'pyinaturalist.oauth_callback.get_auth_code_via_server',
    return_value=_make_server_result('mock_auth_code'),
)
@patch('pyinaturalist.oauth_callback.get_password', return_value='valid_app_secret')
def test_get_access_token_via_auth_code__app_secret_from_keyring(
    mock_get_password, mock_server, mock_get_jwt, requests_mock
):
    requests_mock.post(f'{API_V0}/oauth/token', json=token_accepted_json, status_code=200)

    token = get_access_token_via_auth_code(app_id='valid_app_id', use_pkce=False)
    assert token == JWT_API_TOKEN
    submitted_json = requests_mock.last_request.json()
    assert submitted_json['client_secret'] == 'valid_app_secret'
    mock_get_password.assert_called_once_with(KEYRING_KEY, 'app_secret')


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', side_effect=[NOT_CACHED_RESPONSE, JWT_RESPONSE_200])
@patch(
    'pyinaturalist.oauth_callback.get_auth_code_via_server',
    return_value=_make_server_result('mock_auth_code'),
)
@patch('pyinaturalist.oauth_callback.get_password', return_value='valid_app_id')
def test_get_access_token_via_auth_code__app_id_from_keyring(
    mock_get_password, mock_server, mock_get_jwt, requests_mock
):
    requests_mock.post(f'{API_V0}/oauth/token', json=token_accepted_json, status_code=200)

    token = get_access_token_via_auth_code()
    assert token == JWT_API_TOKEN
    submitted_json = requests_mock.last_request.json()
    assert submitted_json['client_id'] == 'valid_app_id'
    mock_get_password.assert_called_once_with(KEYRING_KEY, 'app_id')


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', return_value=NOT_CACHED_RESPONSE)
@pytest.mark.parametrize(
    'auth_error, match',
    [
        ('access_denied', 'access_denied'),
        ('state_mismatch', 'state parameter mismatch'),
    ],
)
def test_get_access_token_via_auth_code__server_error(mock_get_jwt, auth_error, match):
    """Authorization errors from the callback server raise AuthenticationError."""
    with patch(
        'pyinaturalist.oauth_callback.get_auth_code_via_server',
        return_value=_make_server_result(auth_error=auth_error),
    ):
        with pytest.raises(AuthenticationError, match=match):
            get_access_token_via_auth_code(app_id='valid_app_id')


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', return_value=NOT_CACHED_RESPONSE)
@patch('pyinaturalist.oauth_callback.HTTPServer', side_effect=OSError(98, 'Address already in use'))
def test_get_access_token_via_auth_code__port_in_use(mock_httpserver, mock_get_jwt):
    """An OSError when binding the callback server raises AuthenticationError."""
    with pytest.raises(AuthenticationError, match='port'):
        get_access_token_via_auth_code(app_id='valid_app_id')


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', side_effect=[NOT_CACHED_RESPONSE, JWT_RESPONSE_200])
@patch(
    'pyinaturalist.oauth_callback.get_auth_code_via_server',
    return_value=_make_server_result('mock_auth_code'),
)
def test_get_access_token_via_auth_code__custom_open_url(mock_server, mock_get_jwt, requests_mock):
    """A custom open_url callback is forwarded to get_auth_code_via_server."""
    requests_mock.post(f'{API_V0}/oauth/token', json=token_accepted_json, status_code=200)

    custom_open_url = lambda url: None  # noqa: E731
    get_access_token_via_auth_code(app_id='valid_app_id', open_url=custom_open_url)

    _, call_kwargs = mock_server.call_args
    assert call_kwargs['open_url'] is custom_open_url


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', side_effect=[NOT_CACHED_RESPONSE, JWT_RESPONSE_200])
@patch('pyinaturalist.oauth_callback.webbrowser.open')
def test_get_access_token_via_auth_code__custom_get_code_oob(
    mock_browser, mock_get_jwt, requests_mock
):
    """A custom get_code callback is used instead of input() in OOB mode."""
    requests_mock.post(f'{API_V0}/oauth/token', json=token_accepted_json, status_code=200)
    received_urls = []

    def my_get_code(url: str) -> str:
        received_urls.append(url)
        return 'custom_oob_code'

    token = get_access_token_via_auth_code(
        app_id='valid_app_id', use_oob=True, get_code=my_get_code
    )
    assert token == JWT_API_TOKEN
    assert len(received_urls) == 1
    assert 'inaturalist.org' in received_urls[0]
    submitted_json = requests_mock.last_request.json()
    assert submitted_json['code'] == 'custom_oob_code'


# validate_token
# --------------


@pytest.mark.parametrize('response_code', [200, 401, 403, 502])
def test_validate_token(response_code):
    with patch.object(ClientSession, 'send', return_value=Response()) as mock_get:
        mock_get.return_value.status_code = response_code
        assert validate_token('token') == (response_code == 200)


# get_keyring_credentials
# -------------------------


@patch('pyinaturalist.auth.get_password', side_effect=list(MOCK_CREDS_OAUTH.values()))
def test_get_keyring_credentials(get_password):
    assert get_keyring_credentials() == MOCK_CREDS_OAUTH


@patch('pyinaturalist.auth.get_password', side_effect=KeyringError)
def test_get_keyring_credentials__no_backend(get_password):
    assert get_keyring_credentials() == {}


# set_keyring_credentials
# -------------------------


@patch('pyinaturalist.auth.set_password')
def test_set_keyring_credentials(set_password):
    set_keyring_credentials('username', 'password', 'app_id', 'app_secret')
    assert set_password.call_count == 4


# _decode_jwt_exp
# ---------------


@pytest.mark.parametrize(
    'payload, expected_exp',
    [
        ({'exp': 1893456000}, 1893456000),  # valid exp claim
        ({}, None),  # no exp claim
    ],
)
def test_decode_jwt_exp(payload, expected_exp):
    token = make_jwt(payload)
    result = _decode_jwt_exp(token)
    if expected_exp is None:
        assert result is None
    else:
        assert result is not None
        assert result.tzinfo == timezone.utc
        assert int(result.timestamp()) == expected_exp


@pytest.mark.parametrize(
    'bad_token',
    [
        'not.a.jwt.with.extra.parts',  # too many parts
        'onlyone',  # not enough parts
        'bad.%%%%.sig',  # invalid base64
    ],
)
def test_decode_jwt_exp__invalid_token_returns_none(bad_token):
    assert _decode_jwt_exp(bad_token) is None
