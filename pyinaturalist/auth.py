from logging import getLogger
from os import getenv
from typing import Dict, Optional

from keyring import get_password, set_password
from keyring.errors import KeyringError

from pyinaturalist.api_requests import post
from pyinaturalist.constants import API_V0_BASE_URL, KEYRING_KEY
from pyinaturalist.exceptions import AuthenticationError

logger = getLogger(__name__)


def get_access_token(
    username: str = None,
    password: str = None,
    app_id: str = None,
    app_secret: str = None,
    user_agent: str = None,
) -> str:
    """Get an access token using the user's iNaturalist username and password, using the
    Resource Owner Password Credentials Flow. Requires registering an iNaturalist app.

    **API reference:** https://www.inaturalist.org/pages/api+reference#auth

    See :ref:`auth` for additional options for storing credentials.

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
        user_agent: A custom user-agent string to provide to the iNaturalist API

    Raises:
        :py:exc:`requests.HTTPError` (401) if credentials are invalid
    """
    payload = {
        'username': username or getenv('INAT_USERNAME'),
        'password': password or getenv('INAT_PASSWORD'),
        'client_id': app_id or getenv('INAT_APP_ID'),
        'client_secret': app_secret or getenv('INAT_APP_SECRET'),
        'grant_type': 'password',
    }

    # If neither args nor envars were given, then check the keyring
    if not all(payload.values()):
        payload.update(get_keyring_credentials())
    if all(payload.values()):
        logger.info('Retrieved credentials from keyring')
    else:
        raise AuthenticationError('Not all authentication parameters were provided')

    response = post(f'{API_V0_BASE_URL}/oauth/token', json=payload, user_agent=user_agent)
    response.raise_for_status()
    return response.json()['access_token']


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
