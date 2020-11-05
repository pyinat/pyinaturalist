from logging import getLogger
from os import getenv
from typing import Dict

from pyinaturalist.exceptions import AuthenticationError
from pyinaturalist.api_requests import post
from pyinaturalist.constants import INAT_KEYRING_KEY, INAT_BASE_URL

logger = getLogger(__name__)


def get_access_token(
    username: str = None,
    password: str = None,
    app_id: str = None,
    app_secret: str = None,
    user_agent: str = None,
) -> str:
    """Get an access token using the user's iNaturalist username and password.
    You still need an iNaturalist app to do this.

    **API reference:** https://www.inaturalist.org/pages/api+reference#auth

    **Environment Variables**

    Alternatively, you may provide credentials via environment variables instead. The
    environment variable names are the keyword arguments in uppercase, prefixed with ``INAT_``:

    * ``INAT_USERNAME``
    * ``INAT_PASSWORD``
    * ``INAT_APP_ID``
    * ``INAT_APP_SECRET``

    .. admonition:: Set environment variables in python:
        :class: toggle

        >>> import os
        >>> os.environ['INAT_USERNAME'] = 'my_username'
        >>> os.environ['INAT_PASSWORD'] = 'my_password'
        >>> os.environ['INAT_APP_ID'] = '33f27dc63bdf27f4ca6cd95dd9dcd5df'
        >>> os.environ['INAT_APP_SECRET'] = 'bbce628be722bfe2abd5fc566ba83de4'

    .. admonition:: Set environment variables in a POSIX shell (bash, etc.):
        :class: toggle

        .. code-block:: bash

            export INAT_USERNAME="my_username"
            export INAT_PASSWORD="my_password"
            export INAT_APP_ID="33f27dc63bdf27f4ca6cd95dd9dcd5df"
            export INAT_APP_SECRET="bbce628be722bfe2abd5fc566ba83de4"

    .. admonition:: Set environment variables in a Windows shell:
        :class: toggle

        .. code-block:: bat

            set INAT_USERNAME="my_username"
            set INAT_PASSWORD="my_password"
            set INAT_APP_ID="33f27dc63bdf27f4ca6cd95dd9dcd5df"
            set INAT_APP_SECRET="bbce628be722bfe2abd5fc566ba83de4"

    .. admonition:: Set environment variables in PowerShell:
        :class: toggle

        .. code-block:: powershell

            $Env:INAT_USERNAME="my_username"
            $Env:INAT_PASSWORD="my_password"
            $Env:INAT_APP_ID="33f27dc63bdf27f4ca6cd95dd9dcd5df"
            $Env:INAT_APP_SECRET="bbce628be722bfe2abd5fc566ba83de4"

    **Keyring Integration**

    To handle your credentials more securely, you can store them in your system keyring.
    Most common keyring bakcends are supported, including:

    * macOS `Keychain
      <https://en.wikipedia.org/wiki/Keychain_%28software%29>`_
    * Freedesktop `Secret Service
      <http://standards.freedesktop.org/secret-service/>`_
    * KDE4 & KDE5 `KWallet <https://en.wikipedia.org/wiki/KWallet>`_
    * `Windows Credential Locker
      <https://docs.microsoft.com/en-us/windows/uwp/security/credential-locker>`_

    See `python keyring documentation <https://github.com/jaraco/keyring>`_ for more details.

    To store your credentials in the keyring, run:

        >>> from pyinaturalist.auth import set_keyring_credentials
        >>> set_keyring_credentials(
        >>>     username='my_username',
        >>>     password='my_password',
        >>>     app_id='33f27dc63bdf27f4ca6cd95dd9dcd5df',
        >>>     app_secret='bbce628be722bfe2abd5fc566ba83de4',
        >>> )

    Afterward, you can call ``get_access_token()`` without any arguments, and your credentials
    will be retrieved from the keyring.

    **Password Manager Integration**

    Keyring integration can be taken a step further by managing your keyring with a password
    manager. This has the advantage of keeping your credentials in one place that can be synced
    across multiple machines. `KeePassXC <https://keepassxc.org/>`_ offers this feature for
    macOS and Linux systems. See this guide for setup info:
    `KeepassXC and secret service, a small walk-through
    <https://avaldes.co/2020/01/28/secret-service-keepassxc.html>`_

    Examples:

        With direct keyword arguments:

        >>> from pyinaturalist.auth import get_access_token
        >>> access_token = get_access_token(
        >>>     username='my_username',
        >>>     password='my_password',
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
        username: iNaturalist username
        password: iNaturalist password
        app_id: iNaturalist application ID
        app_secret: iNaturalist application secret
        user_agent: a user-agent string that will be passed to iNaturalist.

    Raises:
        :py:exc:`requests.HTTPError` (401) if credentials are invalid
    """
    payload = {
        "username": username or getenv("INAT_USERNAME"),
        "password": password or getenv("INAT_PASSWORD"),
        "client_id": app_id or getenv("INAT_APP_ID"),
        "client_secret": app_secret or getenv("INAT_APP_SECRET"),
        "grant_type": "password",
    }

    # If neither args nor envars were given, then check the keyring
    if not all(payload.values()):
        payload.update(get_keyring_credentials())
    if not all(payload.values()):
        raise AuthenticationError("Not all authentication parameters were provided")

    response = post(
        f"{INAT_BASE_URL}/oauth/token",
        json=payload,
        user_agent=user_agent,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_keyring_credentials() -> Dict[str, str]:
    """Attempt to get iNaturalist credentials from the system keyring

    Returns:
        OAuth-compatible credentials dict
    """
    # Quietly fail if keyring package is not installed
    try:
        from keyring import get_password
        from keyring.errors import KeyringError
    except ImportError:
        logger.warning("Optional dependency `keyring` not installed")
        return {}

    # Quietly fail if keyring backend is not available
    try:
        return {
            "username": get_password(INAT_KEYRING_KEY, "username"),
            "password": get_password(INAT_KEYRING_KEY, "password"),
            "client_id": get_password(INAT_KEYRING_KEY, "app_id"),
            "client_secret": get_password(INAT_KEYRING_KEY, "app_secret"),
        }
    except KeyringError as e:
        logger.warning(str(e))
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
    from keyring import set_password

    set_password(INAT_KEYRING_KEY, "username", username)
    set_password(INAT_KEYRING_KEY, "password", password)
    set_password(INAT_KEYRING_KEY, "app_id", app_id)
    set_password(INAT_KEYRING_KEY, "app_secret", app_secret)
