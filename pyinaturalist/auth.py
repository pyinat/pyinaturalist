from logging import getLogger
from os import getenv
from typing import Dict, Optional

from keyring import get_password, set_password
from keyring.errors import KeyringError
from requests import Response

from pyinaturalist.constants import API_V0, JWT_EXPIRATION, KEYRING_KEY
from pyinaturalist.exceptions import AuthenticationError
from pyinaturalist.session import ClientSession, get_local_session

logger = getLogger(__name__)


def get_access_token(
    username: Optional[str] = None,
    password: Optional[str] = None,
    app_id: Optional[str] = None,
    app_secret: Optional[str] = None,
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


def get_keyring_credentials() -> Dict[str, Optional[str]]:
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
        expire_after=JWT_EXPIRATION,  # type: ignore
        only_if_cached=only_if_cached,  # If True, will return a 504 if not cached
        raise_for_status=False,
    )
