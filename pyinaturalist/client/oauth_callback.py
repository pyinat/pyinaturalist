import base64
import hashlib
import hmac
import html
import secrets
import threading
import time
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from logging import getLogger
from os import getenv
from urllib.parse import parse_qs, urlencode, urlparse

from keyring import get_password
from keyring.errors import KeyringError

from pyinaturalist.constants import KEYRING_KEY, OAUTH_AUTHORIZE_URL
from pyinaturalist.exceptions import AuthenticationError

_logger = getLogger(__name__)


def get_auth_code_via_server(
    authorize_url: str,
    port: int,
    timeout: int,
    state: str | None = None,
    open_url: Callable[[str], None] | None = None,
) -> 'CallbackResult':
    """Start a local HTTP server, open the browser for authorization, and wait for the callback.

    Args:
        authorize_url: The full authorization URL to open in the browser.
        port: Port for the local callback server.
        timeout: Seconds to wait for the callback.
        state: Expected state value for CSRF protection; ``None`` disables the check.
        open_url: Callback to open the authorization URL. Defaults to ``webbrowser.open``.

    Returns:
        A :py:class:`CallbackResult` with ``auth_code`` or ``auth_error`` set.

    Raises:
        :py:exc:`.AuthenticationError`: if the port is already in use.
    """
    handler_class, result = _make_callback_handler(state)

    try:
        server = HTTPServer(('127.0.0.1', port), handler_class)
    except OSError as e:
        raise AuthenticationError(
            f'Could not start callback server on port {port}: {e}. '
            f"Try a different port with the 'port' parameter."
        ) from e

    def _serve_until_result():
        """Handle requests in a loop until a code or error is received, or timeout expires."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            server.timeout = max(0, deadline - time.monotonic())
            try:
                server.handle_request()
            except Exception as e:
                _logger.exception(e)
                break
            if result.auth_code or result.auth_error:
                break

    # Note: if the server thread raises an unhandled exception, it will be lost (daemon thread).
    # The caller will see 'No authorization code received' after the join timeout expires.
    server_thread = threading.Thread(target=_serve_until_result, daemon=True)
    server_thread.start()

    _logger.info('Opening browser for authorization: %s', authorize_url)
    (open_url or webbrowser.open)(authorize_url)

    try:
        server_thread.join(timeout)
    finally:
        server.server_close()

    return result


def build_authorize_url(
    app_id: str,
    redirect_uri: str,
    code_challenge: str | None = None,
    state: str | None = None,
) -> str:
    """Build the OAuth2 authorization URL.

    Args:
        app_id: OAuth2 application ID (client ID).
        redirect_uri: The redirect URI registered with your iNaturalist application.
        code_challenge: PKCE code challenge (base64url-encoded SHA256 of the verifier).
        state: Optional random state value for CSRF protection.

    Returns:
        The full authorization URL to open in the user's browser.
    """
    params: dict[str, str] = {
        'client_id': app_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
    }
    if code_challenge:
        params['code_challenge'] = code_challenge
        params['code_challenge_method'] = 'S256'
    if state:
        params['state'] = state
    return f'{OAUTH_AUTHORIZE_URL}?{urlencode(params)}'


def _generate_pkce_pair() -> tuple[str, str]:
    """Generate a PKCE code verifier and challenge per RFC 7636.

    Returns:
        A tuple of ``(code_verifier, code_challenge)``
    """
    code_verifier = secrets.token_urlsafe(64)  # 86 chars
    digest = hashlib.sha256(code_verifier.encode('ascii')).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')
    return code_verifier, code_challenge


def _resolve_auth_code_creds(
    app_id: str | None,
    app_secret: str | None,
    use_pkce: bool,
) -> tuple[str, str | None]:
    """Resolve app_id and app_secret from arguments, environment variables, or keyring."""
    app_id = app_id or getenv('INAT_APP_ID')
    if not use_pkce:
        app_secret = app_secret or getenv('INAT_APP_SECRET')
    if not app_id or (not use_pkce and not app_secret):
        try:
            if not app_id:
                app_id = get_password(KEYRING_KEY, 'app_id')
            if not use_pkce and not app_secret:
                app_secret = get_password(KEYRING_KEY, 'app_secret')
        except KeyringError as e:
            _logger.warning(e)
    if not app_id:
        raise AuthenticationError('app_id is required for authorization code flow')
    if not use_pkce and not app_secret:
        raise AuthenticationError('app_secret is required when use_pkce=False')
    return app_id, app_secret


def _build_token_payload(
    app_id: str,
    auth_code: str,
    redirect_uri: str,
    code_verifier: str | None,
    app_secret: str | None,
    use_pkce: bool,
) -> dict[str, str]:
    """Build the POST payload for the token exchange."""
    payload: dict[str, str] = {
        'client_id': app_id,
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
    }
    if use_pkce and code_verifier:
        payload['code_verifier'] = code_verifier
    elif not use_pkce and app_secret:
        payload['client_secret'] = app_secret
    return payload


def _obtain_auth_code(
    authorize_url: str,
    *,
    use_oob: bool,
    port: int,
    timeout: int,
    state: str | None = None,
    open_url: Callable[[str], None] | None = None,
    get_code: Callable[[str], str] | None = None,
) -> str:
    """Open the browser and obtain an authorization code via OOB or local server."""
    if use_oob:
        _logger.info('Opening browser for authorization: %s', authorize_url)
        (open_url or webbrowser.open)(authorize_url)
        if get_code:
            return get_code(authorize_url)
        return input('Enter the authorization code from iNaturalist: ').strip()

    result = get_auth_code_via_server(
        authorize_url, port=port, timeout=timeout, state=state, open_url=open_url
    )
    if result.auth_code is None:
        if result.auth_error == 'state_mismatch':
            raise AuthenticationError(
                'Authorization failed: state parameter mismatch (possible CSRF attack)'
            )
        elif result.auth_error:
            raise AuthenticationError(f'Authorization failed: {result.auth_error}')
        raise AuthenticationError('No authorization code received (timed out or cancelled)')
    return result.auth_code


@dataclass
class CallbackResult:
    """Holds the result of a single OAuth callback request."""

    auth_code: str | None = None
    auth_error: str | None = None


def _make_callback_handler(
    expected_state: str | None,
) -> tuple[type[BaseHTTPRequestHandler], CallbackResult]:
    """Create a fresh handler class bound to a per-request CallbackResult.

    Using a factory avoids class-level mutable state, making concurrent or
    sequential calls safe without manual cleanup.

    Returns:
        A tuple of ``(handler_class, result)`` where ``result`` is populated
        in-place when the HTTP callback arrives.
    """
    result = CallbackResult()

    class _OAuthCallbackHandler(BaseHTTPRequestHandler):
        """HTTP request handler that captures an OAuth authorization code from a redirect."""

        def do_GET(self):
            """Handle the OAuth callback GET request."""
            query = parse_qs(urlparse(self.path).query)

            received_state = query.get('state', [None])[0]
            # Use hmac.compare_digest to avoid timing issues; skip when state is not expected
            state_mismatch = expected_state is not None and not hmac.compare_digest(
                received_state or '', expected_state
            )
            if state_mismatch:
                result.auth_error = 'state_mismatch'
                self.send_response(400)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(
                    b'<html><body><h1>Authorization failed</h1>'
                    b'<p>State parameter mismatch. This may indicate a CSRF attack.</p>'
                    b'</body></html>'
                )
                return

            code_values = query.get('code')
            if code_values:
                result.auth_code = code_values[0]
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(
                    b'<html><body><h1>Authorization successful!</h1>'
                    b'<p>You can close this tab and return to your application.</p>'
                    b'</body></html>'
                )
            else:
                error = query.get('error', ['unknown'])[0]
                result.auth_error = error
                self.send_response(400)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(
                    f'<html><body><h1>Authorization failed</h1>'
                    f'<p>Error: {html.escape(error)}</p></body></html>'.encode()
                )

        def log_message(self, format: str, *args: object):
            """Route HTTP server logs through the module _logger."""
            _logger.debug(format, *args)

    return _OAuthCallbackHandler, result
