import base64
import hashlib
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from logging import getLogger
from os import getenv
from typing import Optional
from urllib.parse import parse_qs, urlencode, urlparse

from keyring import get_password, set_password
from keyring.errors import KeyringError
from requests import HTTPError, Response

from pyinaturalist.constants import API_V0, API_V1, KEYRING_KEY, OAUTH_AUTHORIZE_URL
from pyinaturalist.exceptions import AuthenticationError
from pyinaturalist.session import ClientSession, get_local_session

logger = getLogger(__name__)


def get_access_token(
    username: str | None = None,
    password: str | None = None,
    app_id: str | None = None,
    app_secret: str | None = None,
    jwt: bool = True,
    refresh: bool = False,
) -> str:
    """Get an access token using the user's iNaturalist username and password, using the
    Resource Owner Password Credentials Flow. Requires registering an iNaturalist app.

    .. rubric:: Notes

    * API reference: https://www.inaturalist.org/pages/api+reference#auth
    * See :ref:`auth` for additional options for storing credentials.
    * This can be used to get either a JWT or OAuth token. These can be used interchangeably for
      many endpoints. JWT is preferred for newer endpoints.

    Examples:

        With direct keyword arguments:

        >>> from pyinaturalist import get_access_token
        >>> access_token = get_access_token(
        >>>     username='my_inaturalist_username',
        >>>     password='my_inaturalist_password',
        >>>     app_id='33f27dc63bdf27f4ca6cd95dd9dcd5df',
        >>>     app_secret='bbce628be722bfe2abd5fc566ba83de4',
        >>> )

        With environment variables or keyring configured:

        >>> access_token = get_access_token()

        If you would like to run custom requests for endpoints not yet implemented in pyinaturalist,
        you can authenticate these requests by putting the token in your HTTP headers as follows:

        >>> import requests
        >>> requests.get(
        >>>     'https://www.inaturalist.org/observations/1234',
        >>>      headers={'Authorization': f'Bearer {access_token}'},
        >>> )

    Args:
        username: iNaturalist username (same as the one you use to login on inaturalist.org)
        password: iNaturalist password (same as the one you use to login on inaturalist.org)
        app_id: OAuth2 application ID
        app_secret: OAuth2 application secret
        jwt: Return a JSON Web Token; otherwise return an OAuth2 access token.
        refresh: Do not use any cached tokens, even if they are not expired

    Raises:
        :py:exc:`requests.HTTPError`: (401) if credentials are invalid
    """
    # First check if we have a previously cached JWT
    session = get_local_session()
    response = _get_jwt(session, only_if_cached=True)
    if response.ok and not refresh:
        logger.info('Using cached access token')
        return response.json()['api_token']

    # Otherwise check for credentials in either args or environment variables
    payload = {
        'username': username or getenv('INAT_USERNAME'),
        'password': password or getenv('INAT_PASSWORD'),
        'client_id': app_id or getenv('INAT_APP_ID'),
        'client_secret': app_secret or getenv('INAT_APP_SECRET'),
        'grant_type': 'password',
    }

    # If any fields were missing, then check the keyring
    if not all(payload.values()):
        payload.update(get_keyring_credentials())
        if all(payload.values()):
            logger.info('Retrieved credentials from keyring')
        else:
            raise AuthenticationError(
                'Not all authentication parameters were provided', response=response
            )

    # Get OAuth access token
    response = session.post(f'{API_V0}/oauth/token', json=payload)
    response.raise_for_status()
    access_token = response.json()['access_token']

    # If specified, use OAuth token to get (and cache) a JWT
    if jwt:
        response = _get_jwt(session, access_token)
        response.raise_for_status()
        access_token = response.json()['api_token']
    return access_token


def get_access_token_via_auth_code(
    app_id: Optional[str] = None,
    app_secret: Optional[str] = None,
    use_pkce: bool = True,
    use_oob: bool = False,
    jwt: bool = True,
    refresh: bool = False,
    port: int = 8080,
    timeout: int = 120,
) -> str:
    """Get an access token using the OAuth2 Authorization Code flow, optionally with PKCE.

    This is the recommended approach for CLI and desktop applications because users do not
    need to provide their iNaturalist password to third-party code. Instead, the user
    authenticates directly on inaturalist.org in their browser.

    .. rubric:: Notes

    * Requires registering an iNaturalist application at
      https://www.inaturalist.org/oauth/applications
    * When using PKCE (the default), no client secret is needed.
    * When using the local callback server, register your redirect URI as
      ``http://127.0.0.1:<port>`` (e.g., ``http://127.0.0.1:8080``).
    * When using OOB mode, register your redirect URI as
      ``urn:ietf:wg:oauth:2.0:oob``.

    Examples:

        With PKCE (recommended, no client secret needed):

        >>> from pyinaturalist import get_access_token_via_auth_code
        >>> access_token = get_access_token_via_auth_code(
        ...     app_id='33f27dc63bdf27f4ca6cd95dd9dcd5df',
        ... )

        Without PKCE (requires client secret):

        >>> access_token = get_access_token_via_auth_code(
        ...     app_id='33f27dc63bdf27f4ca6cd95dd9dcd5df',
        ...     app_secret='bbce628be722bfe2abd5fc566ba83de4',
        ...     use_pkce=False,
        ... )

        For headless/remote environments (OOB mode):

        >>> access_token = get_access_token_via_auth_code(
        ...     app_id='33f27dc63bdf27f4ca6cd95dd9dcd5df',
        ...     use_oob=True,
        ... )

    Args:
        app_id: OAuth2 application ID. Falls back to ``INAT_APP_ID`` env var or keyring.
        app_secret: OAuth2 application secret. Required when ``use_pkce=False``.
        use_pkce: Use PKCE (Proof Key for Code Exchange) instead of a client secret.
        use_oob: Use out-of-band mode: the user manually copies the authorization code
            instead of using a local callback server. Useful for headless environments.
        jwt: Return a JSON Web Token; otherwise return an OAuth2 access token.
        refresh: Do not use any cached tokens, even if they are not expired.
        port: Port for the local callback server. Must match the redirect URI registered
            with your iNaturalist application.
        timeout: Seconds to wait for the user to complete authorization in the browser.

    Raises:
        :py:exc:`.AuthenticationError`: if credentials are missing, the user does not
            authorize in time, or the token exchange fails.
    """
    # First check if we have a previously cached JWT
    session = get_local_session()
    response = _get_jwt(session, only_if_cached=True)
    if response.ok and not refresh:
        logger.info('Using cached access token')
        return response.json()['api_token']

    app_id, app_secret = _resolve_auth_code_creds(app_id, app_secret, use_pkce)

    # Generate PKCE pair if needed
    code_verifier: Optional[str] = None
    code_challenge: Optional[str] = None
    if use_pkce:
        code_verifier, code_challenge = _generate_pkce_pair()

    # Build authorization URL and get the authorization code
    redirect_uri = 'urn:ietf:wg:oauth:2.0:oob' if use_oob else f'http://127.0.0.1:{port}'
    state = secrets.token_urlsafe(16) if not use_oob else None
    authorize_url = _build_authorize_url(app_id, redirect_uri, code_challenge, state)
    auth_code = _obtain_auth_code(
        authorize_url, use_oob=use_oob, port=port, timeout=timeout, state=state
    )

    # Exchange authorization code for access token
    payload = _build_token_payload(
        app_id, auth_code, redirect_uri, code_verifier, app_secret, use_pkce
    )
    response = session.post(f'{API_V0}/oauth/token', json=payload)
    response.raise_for_status()
    access_token = response.json()['access_token']

    # If specified, use OAuth token to get (and cache) a JWT
    if jwt:
        response = _get_jwt(session, access_token)
        response.raise_for_status()
        access_token = response.json()['api_token']
    return access_token


def _resolve_auth_code_creds(
    app_id: Optional[str],
    app_secret: Optional[str],
    use_pkce: bool,
) -> tuple[str, str | None]:
    """Resolve app_id and app_secret from arguments, environment variables, or keyring."""
    app_id = app_id or getenv('INAT_APP_ID')
    if not use_pkce:
        app_secret = app_secret or getenv('INAT_APP_SECRET')
    if not app_id:
        try:
            app_id = get_password(KEYRING_KEY, 'app_id')
            if not use_pkce and not app_secret:
                app_secret = get_password(KEYRING_KEY, 'app_secret')
        except KeyringError as e:
            logger.warning(e)
    if not app_id:
        raise AuthenticationError('app_id is required for authorization code flow')
    if not use_pkce and not app_secret:
        raise AuthenticationError('app_secret is required when use_pkce=False')
    return app_id, app_secret


def _build_authorize_url(
    app_id: str,
    redirect_uri: str,
    code_challenge: Optional[str] = None,
    state: Optional[str] = None,
) -> str:
    """Build the OAuth2 authorization URL."""
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


def _obtain_auth_code(
    authorize_url: str,
    *,
    use_oob: bool,
    port: int,
    timeout: int,
    state: Optional[str] = None,
) -> str:
    """Open the browser and obtain an authorization code via OOB or local server."""
    if use_oob:
        logger.info('Opening browser for authorization: %s', authorize_url)
        webbrowser.open(authorize_url)
        return input('Enter the authorization code from iNaturalist: ').strip()

    _OAuthCallbackHandler.expected_state = state
    auth_code = _get_auth_code_via_server(authorize_url, port=port, timeout=timeout)
    if not auth_code:
        error = _OAuthCallbackHandler.auth_error
        if error == 'state_mismatch':
            raise AuthenticationError(
                'Authorization failed: state parameter mismatch (possible CSRF attack)'
            )
        elif error:
            raise AuthenticationError(f'Authorization failed: {error}')
        raise AuthenticationError('No authorization code received (timed out or cancelled)')
    return auth_code


def _build_token_payload(
    app_id: str,
    auth_code: str,
    redirect_uri: str,
    code_verifier: Optional[str],
    app_secret: Optional[str],
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


def _generate_pkce_pair() -> tuple[str, str]:
    """Generate a PKCE code verifier and challenge per RFC 7636.

    Returns:
        A tuple of ``(code_verifier, code_challenge)``
    """
    code_verifier = secrets.token_urlsafe(64)  # 86 chars
    digest = hashlib.sha256(code_verifier.encode('ascii')).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')
    return code_verifier, code_challenge


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler that captures an OAuth authorization code from a redirect callback.

    Note: ``auth_code``, ``auth_error``, and ``expected_state`` are class variables so they
    can be read from the calling thread after ``handle_request()`` completes. This is safe for
    sequential use but not thread-safe under concurrent calls.
    """

    auth_code: Optional[str] = None
    auth_error: Optional[str] = None
    expected_state: Optional[str] = None

    def do_GET(self) -> None:
        """Handle the OAuth callback GET request."""
        query = parse_qs(urlparse(self.path).query)

        received_state = query.get('state', [None])[0]
        if received_state != _OAuthCallbackHandler.expected_state:
            _OAuthCallbackHandler.auth_error = 'state_mismatch'
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
            _OAuthCallbackHandler.auth_code = code_values[0]
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
            _OAuthCallbackHandler.auth_error = error
            self.send_response(400)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(
                f'<html><body><h1>Authorization failed</h1>'
                f'<p>Error: {error}</p></body></html>'.encode()
            )

    def log_message(self, format: str, *args: object) -> None:
        """Route HTTP server logs through the module logger."""
        logger.debug(format, *args)


def _get_auth_code_via_server(authorize_url: str, port: int, timeout: int) -> Optional[str]:
    """Start a local HTTP server, open the browser for authorization, and wait for the callback.

    Args:
        authorize_url: The full authorization URL to open in the browser.
        port: Port for the local callback server.
        timeout: Seconds to wait for the callback.

    Returns:
        The authorization code, or ``None`` if it timed out or was denied.

    Raises:
        :py:exc:`.AuthenticationError`: if the port is already in use.
    """
    _OAuthCallbackHandler.auth_code = None
    _OAuthCallbackHandler.auth_error = None

    try:
        server = HTTPServer(('127.0.0.1', port), _OAuthCallbackHandler)
    except OSError as e:
        raise AuthenticationError(
            f'Could not start callback server on port {port}: {e}. '
            f"Try a different port with the 'port' parameter."
        ) from e

    server.timeout = timeout

    server_thread = threading.Thread(target=server.handle_request, daemon=True)
    server_thread.start()

    logger.info('Opening browser for authorization: %s', authorize_url)
    webbrowser.open(authorize_url)

    try:
        server_thread.join()
    finally:
        server.server_close()

    return _OAuthCallbackHandler.auth_code


def validate_token(access_token: str) -> bool:
    """Determine if an access token is valid"""
    session = get_local_session()
    try:
        session.request('GET', f'{API_V1}/users/me', access_token=access_token)
        return True
    except HTTPError:
        return False


def get_keyring_credentials() -> dict[str, str | None]:
    """Attempt to get iNaturalist credentials from the system keyring

    Returns:
        OAuth-compatible credentials dict
    """
    try:
        return {
            'username': get_password(KEYRING_KEY, 'username'),
            'password': get_password(KEYRING_KEY, 'password'),
            'client_id': get_password(KEYRING_KEY, 'app_id'),
            'client_secret': get_password(KEYRING_KEY, 'app_secret'),
        }
    except KeyringError as e:
        logger.warning(e)
        return {}


def set_keyring_credentials(
    username: str,
    password: str,
    app_id: str,
    app_secret: str,
):
    """
    Store iNaturalist credentials in the system keyring for future use.

    Args:
        username: iNaturalist username
        password: iNaturalist password
        app_id: iNaturalist application ID
        app_secret: iNaturalist application secret
    """
    set_password(KEYRING_KEY, 'username', username)
    set_password(KEYRING_KEY, 'password', password)
    set_password(KEYRING_KEY, 'app_id', app_id)
    set_password(KEYRING_KEY, 'app_secret', app_secret)


def _get_jwt(
    session: ClientSession, access_token: str = '', only_if_cached: bool = False
) -> Response:
    return session.get(
        f'{API_V0}/users/api_token',
        headers={'Authorization': f'Bearer {access_token}'},
        only_if_cached=only_if_cached,  # If True, will return a 504 if not cached
        raise_for_status=False,  # type: ignore
    )
