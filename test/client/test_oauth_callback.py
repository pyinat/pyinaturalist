import base64
import hashlib
from http.server import BaseHTTPRequestHandler
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from pyinaturalist.client.oauth_callback import (
    _generate_pkce_pair,
    _make_callback_handler,
    build_authorize_url,
)


def test_generate_pkce_pair():
    verifier, challenge = _generate_pkce_pair()
    # Verifier should be 86 chars (64 bytes base64url-encoded without padding)
    assert len(verifier) == 86
    # Challenge should be the base64url(SHA256(verifier)) without padding
    expected_digest = hashlib.sha256(verifier.encode('ascii')).digest()
    expected_challenge = base64.urlsafe_b64encode(expected_digest).rstrip(b'=').decode('ascii')
    assert challenge == expected_challenge


def test_build_authorize_url__urlencode():
    """redirect_uri with special characters is properly percent-encoded."""
    url = build_authorize_url('my_app', 'http://127.0.0.1:8080', state='abc123')
    assert 'redirect_uri=http%3A%2F%2F127.0.0.1%3A8080' in url
    assert 'state=abc123' in url


def test_build_authorize_url__pkce():
    """PKCE parameters are included when a code_challenge is provided."""
    url = build_authorize_url('my_app', 'http://127.0.0.1:8080', code_challenge='challenge_val')
    assert 'code_challenge=challenge_val' in url
    assert 'code_challenge_method=S256' in url


@pytest.fixture
def mock_handler_request():
    """Mocks out the parts of BaseHTTPRequestHandler needed by _OAuthCallbackHandler."""

    def factory(path, expected_state=None):
        handler_class, result = _make_callback_handler(expected_state)

        with (
            patch.object(BaseHTTPRequestHandler, '__init__', return_value=None) as mock_init,
            patch.object(BaseHTTPRequestHandler, 'send_response') as mock_send_response,
            patch.object(BaseHTTPRequestHandler, 'send_header'),
            patch.object(BaseHTTPRequestHandler, 'end_headers'),
        ):
            handler = handler_class(MagicMock(), ('127.0.0.1', 8080), MagicMock())
            handler.path = path
            handler.wfile = BytesIO()
            handler.do_GET()

        mock_init.assert_called_once()
        return {
            'result': result,
            'handler': handler,
            'send_response': mock_send_response,
            'wfile': handler.wfile,
        }

    return factory


def test_handler_get_auth_code(mock_handler_request):
    """The handler correctly extracts an auth code from the callback URL."""
    mocks = mock_handler_request('?code=my_auth_code&state=my_state', expected_state='my_state')
    assert mocks['result'].auth_code == 'my_auth_code'
    assert mocks['result'].auth_error is None
    mocks['send_response'].assert_called_with(200)
    assert b'Authorization successful!' in mocks['wfile'].getvalue()


def test_handler_get_auth_error(mock_handler_request):
    """The handler correctly extracts an error from the callback URL."""
    mocks = mock_handler_request('?error=access_denied&state=my_state', expected_state='my_state')
    assert mocks['result'].auth_code is None
    assert mocks['result'].auth_error == 'access_denied'
    mocks['send_response'].assert_called_with(400)
    assert b'Authorization failed' in mocks['wfile'].getvalue()
    assert b'Error: access_denied' in mocks['wfile'].getvalue()


def test_handler_state_mismatch(mock_handler_request):
    """A state mismatch is detected and reported as a specific error."""
    mocks = mock_handler_request(
        '?code=my_auth_code&state=wrong_state', expected_state='expected_state'
    )
    assert mocks['result'].auth_code is None
    assert mocks['result'].auth_error == 'state_mismatch'
    mocks['send_response'].assert_called_with(400)
    assert b'State parameter mismatch' in mocks['wfile'].getvalue()


def test_handler_no_state_when_expected(mock_handler_request):
    """A missing state parameter when one is expected is a mismatch."""
    mocks = mock_handler_request('?code=my_auth_code', expected_state='expected_state')
    assert mocks['result'].auth_error == 'state_mismatch'
    mocks['send_response'].assert_called_with(400)


def test_handler_state_not_expected(mock_handler_request):
    """If state is not expected, no check is performed."""
    mocks = mock_handler_request('?code=my_auth_code', expected_state=None)
    assert mocks['result'].auth_code == 'my_auth_code'
    assert mocks['result'].auth_error is None
    mocks['send_response'].assert_called_with(200)


def test_handler_unknown_error(mock_handler_request):
    """An unknown error (missing code and error params) is handled."""
    mocks = mock_handler_request('?state=my_state', expected_state='my_state')
    assert mocks['result'].auth_code is None
    assert mocks['result'].auth_error == 'unknown'
    mocks['send_response'].assert_called_with(400)
