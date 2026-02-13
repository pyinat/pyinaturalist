import base64
import hashlib
import json
import os
from unittest.mock import patch

import pytest
from keyring.errors import KeyringError
from requests import HTTPError, Response

from pyinaturalist.auth import (
    _build_authorize_url,
    _generate_pkce_pair,
    _OAuthCallbackHandler,
    get_access_token,
    get_access_token_via_auth_code,
    get_keyring_credentials,
    set_keyring_credentials,
    validate_token,
)
from pyinaturalist.constants import API_V0
from pyinaturalist.exceptions import AuthenticationError
from pyinaturalist.session import ClientSession
from test.conftest import MOCK_CREDS_ENV, MOCK_CREDS_OAUTH, load_sample_data

token_accepted_json = load_sample_data('get_access_token.json')
token_rejected_json = load_sample_data('get_access_token_401.json')
jwt_json = load_sample_data('get_jwt.json')

@pytest.fixture(autouse=True)
def reset_oauth_handler_state():
    """Reset _OAuthCallbackHandler class state between tests to prevent leakage."""
    _OAuthCallbackHandler.auth_code = None
    _OAuthCallbackHandler.auth_error = None
    _OAuthCallbackHandler.expected_state = None
    yield
    _OAuthCallbackHandler.auth_code = None
    _OAuthCallbackHandler.auth_error = None
    _OAuthCallbackHandler.expected_state = None


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
def test_get_access_token__oauth(mock_get_jwt, requests_mock):
    requests_mock.post(
        f'{API_V0}/oauth/token',
        json=token_accepted_json,
        status_code=200,
    )

    token = get_access_token(
        'valid_username', 'valid_password', 'valid_app_id', 'valid_app_secret', jwt=False
    )
    assert token == OAUTH_ACCESS_TOKEN


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', side_effect=[NOT_CACHED_RESPONSE, JWT_RESPONSE_200])
def test_get_access_token__jwt(mock_get_jwt, requests_mock):
    requests_mock.post(
        f'{API_V0}/oauth/token',
        json=token_accepted_json,
        status_code=200,
    )

    token = get_access_token('valid_username', 'valid_password', 'valid_app_id', 'valid_app_secret')
    assert token == JWT_API_TOKEN


@patch.dict(os.environ, {}, clear=True)
def test_get_access_token__cached_jwt(requests_mock):
    """An initial request will return a 200 if a JWT is already cached, or a 504 otherwise."""
    requests_mock.post(
        f'{API_V0}/oauth/token',
        json=token_accepted_json,
        status_code=200,
    )
    requests_mock.get(
        f'{API_V0}/users/api_token',
        json=jwt_json,
        status_code=200,
    )

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
    requests_mock.post(
        f'{API_V0}/oauth/token',
        json=token_accepted_json,
        status_code=200,
    )

    token = get_access_token()
    assert token == JWT_API_TOKEN
    mock_keyring_credentials.assert_not_called()


@patch.dict(
    os.environ,
    {
        'INAT_USERNAME': 'valid_username',
        'INAT_PASSWORD': 'valid_password',
    },
)
@patch('pyinaturalist.auth._get_jwt', side_effect=[NOT_CACHED_RESPONSE, JWT_RESPONSE_200])
def test_get_access_token__mixed_args_and_envars(mock_get_jwt, requests_mock):
    requests_mock.post(
        f'{API_V0}/oauth/token',
        json=token_accepted_json,
        status_code=200,
    )

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
    requests_mock.post(
        f'{API_V0}/oauth/token',
        json=token_accepted_json,
        status_code=200,
    )

    get_access_token()
    submitted_json = mock_post.call_args[1]['json']
    assert submitted_json == {'grant_type': 'password', **MOCK_CREDS_OAUTH}
    mock_keyring_credentials.assert_called()


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth.get_keyring_credentials')
@patch('pyinaturalist.auth._get_jwt', return_value=NOT_CACHED_RESPONSE)
def test_get_access_token__missing_creds(mock_get_jwt, mock_keyring_credentials):
    with pytest.raises(AuthenticationError):
        get_access_token('username')


@patch('pyinaturalist.auth._get_jwt', return_value=NOT_CACHED_RESPONSE)
def test_get_access_token__invalid_creds(mock_get_jwt, requests_mock):
    requests_mock.post(
        f'{API_V0}/oauth/token',
        json=token_rejected_json,
        status_code=401,
    )

    with pytest.raises(HTTPError):
        get_access_token('username', 'password', 'app_id', 'app_secret')


# get_access_token_via_auth_code
# -----------------------------------


def test_generate_pkce_pair():
    verifier, challenge = _generate_pkce_pair()
    # Verifier should be 86 chars (64 bytes base64url-encoded without padding)
    assert len(verifier) == 86
    # Challenge should be the base64url(SHA256(verifier)) without padding
    expected_digest = hashlib.sha256(verifier.encode('ascii')).digest()
    expected_challenge = base64.urlsafe_b64encode(expected_digest).rstrip(b'=').decode('ascii')
    assert challenge == expected_challenge


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', side_effect=[NOT_CACHED_RESPONSE, JWT_RESPONSE_200])
@patch('pyinaturalist.auth.webbrowser.open')
@patch('pyinaturalist.auth._get_auth_code_via_server', return_value='mock_auth_code')
def test_get_access_token_via_auth_code__pkce(
    mock_server, mock_browser, mock_get_jwt, requests_mock
):
    requests_mock.post(
        f'{API_V0}/oauth/token',
        json=token_accepted_json,
        status_code=200,
    )

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
@patch('pyinaturalist.auth.webbrowser.open')
@patch('pyinaturalist.auth._get_auth_code_via_server', return_value='mock_auth_code')
def test_get_access_token_via_auth_code__no_pkce(
    mock_server, mock_browser, mock_get_jwt, requests_mock
):
    requests_mock.post(
        f'{API_V0}/oauth/token',
        json=token_accepted_json,
        status_code=200,
    )

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
@patch('pyinaturalist.auth.webbrowser.open')
@patch('builtins.input', return_value='oob_auth_code')
def test_get_access_token_via_auth_code__oob(mock_input, mock_browser, mock_get_jwt, requests_mock):
    requests_mock.post(
        f'{API_V0}/oauth/token',
        json=token_accepted_json,
        status_code=200,
    )

    token = get_access_token_via_auth_code(app_id='valid_app_id', use_oob=True)
    assert token == JWT_API_TOKEN
    mock_input.assert_called_once()
    mock_browser.assert_called_once()

    # Verify the redirect_uri is OOB
    submitted_json = requests_mock.last_request.json()
    assert submitted_json['redirect_uri'] == 'urn:ietf:wg:oauth:2.0:oob'
    assert submitted_json['code'] == 'oob_auth_code'


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', return_value=JWT_RESPONSE_200)
def test_get_access_token_via_auth_code__cached_jwt(mock_get_jwt):
    """If a JWT is already cached, return it without starting the browser flow."""
    token = get_access_token_via_auth_code(app_id='valid_app_id')
    assert token == JWT_API_TOKEN


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', return_value=NOT_CACHED_RESPONSE)
@patch('pyinaturalist.auth.webbrowser.open')
@patch('pyinaturalist.auth._get_auth_code_via_server', return_value=None)
def test_get_access_token_via_auth_code__timeout(mock_server, mock_browser, mock_get_jwt):
    with pytest.raises(AuthenticationError, match='No authorization code received'):
        get_access_token_via_auth_code(app_id='valid_app_id')


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', return_value=NOT_CACHED_RESPONSE)
def test_get_access_token_via_auth_code__missing_app_id(mock_get_jwt):
    with pytest.raises(AuthenticationError, match='app_id is required'):
        get_access_token_via_auth_code()


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', return_value=NOT_CACHED_RESPONSE)
def test_get_access_token_via_auth_code__missing_app_secret(mock_get_jwt):
    with pytest.raises(AuthenticationError, match='app_secret is required'):
        get_access_token_via_auth_code(app_id='valid_app_id', use_pkce=False)


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', return_value=NOT_CACHED_RESPONSE)
@patch('pyinaturalist.auth.webbrowser.open')
@patch('pyinaturalist.auth._get_auth_code_via_server', return_value=None)
def test_get_access_token_via_auth_code__user_denied(mock_server, mock_browser, mock_get_jwt):
    """When the user denies authorization, the error from the callback is included in the message."""
    _OAuthCallbackHandler.auth_error = 'access_denied'
    with pytest.raises(AuthenticationError, match='access_denied'):
        get_access_token_via_auth_code(app_id='valid_app_id')


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', return_value=NOT_CACHED_RESPONSE)
@patch('pyinaturalist.auth.webbrowser.open')
@patch('pyinaturalist.auth._get_auth_code_via_server', return_value=None)
def test_get_access_token_via_auth_code__state_mismatch(mock_server, mock_browser, mock_get_jwt):
    """A state parameter mismatch raises AuthenticationError with a CSRF message."""
    _OAuthCallbackHandler.auth_error = 'state_mismatch'
    with pytest.raises(AuthenticationError, match='state parameter mismatch'):
        get_access_token_via_auth_code(app_id='valid_app_id')


@patch.dict(os.environ, {}, clear=True)
@patch('pyinaturalist.auth._get_jwt', return_value=NOT_CACHED_RESPONSE)
@patch('pyinaturalist.auth.HTTPServer', side_effect=OSError(98, 'Address already in use'))
def test_get_access_token_via_auth_code__port_in_use(mock_httpserver, mock_get_jwt):
    """An OSError when binding the callback server raises AuthenticationError."""
    with pytest.raises(AuthenticationError, match='port'):
        get_access_token_via_auth_code(app_id='valid_app_id')


def test_build_authorize_url__urlencode():
    """redirect_uri with special characters is properly percent-encoded."""
    url = _build_authorize_url('my_app', 'http://127.0.0.1:8080', state='abc123')
    assert 'redirect_uri=http%3A%2F%2F127.0.0.1%3A8080' in url
    assert 'state=abc123' in url


def test_build_authorize_url__pkce():
    """PKCE parameters are included when a code_challenge is provided."""
    url = _build_authorize_url('my_app', 'http://127.0.0.1:8080', code_challenge='challenge_val')
    assert 'code_challenge=challenge_val' in url
    assert 'code_challenge_method=S256' in url


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


# TODO?
def test_get_keyring_credentials__not_installed():
    pass


@patch('pyinaturalist.auth.get_password', side_effect=KeyringError)
def test_get_keyring_credentials__no_backend(get_password):
    assert get_keyring_credentials() == {}


# get_keyring_credentials
# -------------------------


@patch('pyinaturalist.auth.set_password')
def test_set_keyring_credentials(set_password):
    set_keyring_credentials('username', 'password', 'app_id', 'app_secret')
    assert set_password.call_count == 4
