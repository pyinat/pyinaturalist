import base64
import binascii
import json
import secrets
from collections.abc import Callable
from datetime import datetime, timezone
from logging import getLogger
from os import getenv

from keyring import get_password, set_password
from keyring.errors import KeyringError
from requests import HTTPError, Response

from pyinaturalist.constants import API_V0, API_V1, KEYRING_KEY
from pyinaturalist.exceptions import AuthenticationError
from pyinaturalist.oauth_callback import (
    _build_token_payload,
    _generate_pkce_pair,
    _obtain_auth_code,
    _resolve_auth_code_creds,
    build_authorize_url,
)
from pyinaturalist.session import ClientSession, get_local_session

logger = getLogger(__name__)


def _decode_jwt_exp(token: str) -> datetime | None:
    """Decode the exp claim from a JWT without verifying the signature.

    Returns the expiry as a UTC datetime, or None if the token is not a
    decodable JWT or has no exp claim.
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        # Add padding required by base64
        payload_b64 = parts[1] + '=' * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        exp = payload.get('exp')
        return datetime.fromtimestamp(exp, tz=timezone.utc) if exp else None
    except (ValueError, KeyError, AttributeError, OverflowError, binascii.Error):
        return None


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
    session, cached = _get_cached_jwt(refresh)
    if cached:
        return cached

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
            raise AuthenticationError('Not all authentication parameters were provided')

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
    app_id: str | None = None,
    app_secret: str | None = None,
    use_pkce: bool = True,
    use_oob: bool = False,
    jwt: bool = True,
    refresh: bool = False,
    port: int = 8080,
    timeout: int = 120,
    open_url: Callable[[str], None] | None = None,
    get_code: Callable[[str], str] | None = None,
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
        open_url: Optional callback to open the authorization URL. Defaults to
            ``webbrowser.open``. Useful for testing or custom browser handling.
        get_code: Optional callback for OOB mode that receives the authorization URL and
            returns the authorization code entered by the user. Defaults to ``input()``.

    Raises:
        :py:exc:`.AuthenticationError`: if credentials are missing, the user does not
            authorize in time, or the token exchange fails.
    """
    session, cached = _get_cached_jwt(refresh)
    if cached:
        return cached

    app_id, app_secret = _resolve_auth_code_creds(app_id, app_secret, use_pkce)

    # Generate PKCE pair if needed
    code_verifier: str | None = None
    code_challenge: str | None = None
    if use_pkce:
        code_verifier, code_challenge = _generate_pkce_pair()

    # Build authorization URL and get the authorization code
    redirect_uri = 'urn:ietf:wg:oauth:2.0:oob' if use_oob else f'http://127.0.0.1:{port}'
    state = secrets.token_urlsafe(32) if not use_oob else None
    authorize_url = build_authorize_url(app_id, redirect_uri, code_challenge, state)
    auth_code = _obtain_auth_code(
        authorize_url,
        use_oob=use_oob,
        port=port,
        timeout=timeout,
        state=state,
        open_url=open_url,
        get_code=get_code,
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


def _get_cached_jwt(refresh: bool) -> tuple[ClientSession, str | None]:
    """Return (session, token) if a valid cached JWT exists"""
    session = get_local_session()
    response = _get_jwt(session, only_if_cached=True)
    if response.ok and not refresh:
        logger.info('Using cached access token')
        return session, response.json()['api_token']
    return session, None


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
    session: ClientSession, access_token: str | None = None, only_if_cached: bool = False
) -> Response:
    headers = {'Authorization': f'Bearer {access_token}'} if access_token else {}
    return session.get(
        f'{API_V0}/users/api_token',
        headers=headers,
        only_if_cached=only_if_cached,  # If True, will return a 504 if not cached
        raise_for_status=False,  # type: ignore
    )
