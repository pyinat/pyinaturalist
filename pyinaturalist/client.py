from datetime import datetime
from logging import getLogger
from typing import Any, Callable, Dict

from requests import Session

from pyinaturalist.api_requests import ClientSession
from pyinaturalist.auth import get_access_token
from pyinaturalist.constants import TOKEN_EXPIRATION, JsonResponse
from pyinaturalist.controllers import ObservationController, ProjectController, TaxonController
from pyinaturalist.request_params import get_valid_kwargs, strip_empty_values

logger = getLogger(__name__)


# 'iNatClient' is nonstandard casing, but 'InatClient' just looks wrong. Deal with it, pep8.
class iNatClient:
    """**WIP/Experimental**

    API client class that provides a higher-level interface that is easier to configure, and returns
    :ref:`model objects <models>` instead of JSON. See :ref:`Controller classes <controllers>` for
    request details.

    Examples:
        **Basic usage**

        >>> from pyinaturalist import iNatClient
        >>> client = iNatClient()
        >>> observations = client.observations.search(taxon_name='Danaus plexippus')

        **Authentication**

        Add credentials needed for authenticated requests:
        Note: Passing credentials via environment variables or keyring is preferred

        >>> creds = {
        ...     'username': 'my_inaturalist_username',
        ...     'password': 'my_inaturalist_password',
        ...     'app_id': '33f27dc63bdf27f4ca6cd95dd9dcd5df',
        ...     'app_secret': 'bbce628be722bfe2abd5fc566ba83de4',
        ... }
        >>> client = iNatClient(creds=creds)

        **Default request parameters:**

        Add default ``locale`` and ``preferred_place_id`` request params to pass to any requests
        that use them:

        >>> default_params={'locale': 'en', 'preferred_place_id': 1}
        >>> client = iNatClient(default_params=default_params)

        **Caching, Rate-limiting, and Retries**

        See :py:class:`.ClientSession` and the :ref:`user_guide` for details on these settings.
        ``iNatClient`` will accept any arguments for ``ClientSession``, for example:

        >>> client = iNatClient(per_second=50, expire_after=3600, retries=3)

        Or you can provide your own custom session object:

        >>> session = MyCustomSession(encabulation_factor=47.2)
        >>> client = iNatClient(session=session)

        **Updating settings**

        All settings can also be modified after creating the client:

        >>> client.session = ClientSession()
        >>> client.creds['username'] = 'my_inaturalist_username'
        >>> client.default_params['locale'] = 'es'
        >>> client.dry_run = True

    Args:
        creds: Optional arguments for :py:func:`.get_access_token`, used to get and refresh access
            tokens as needed.
        default_params: Default request parameters to pass to any applicable API requests
        dry_run: Just log all requests instead of sending real requests
        session: Session object to use instead of creating a new one
        kwargs: Keyword arguments for :py:class:`.ClientSession`
    """

    def __init__(
        self,
        creds: Dict[str, str] = None,
        default_params: Dict[str, Any] = None,
        dry_run: bool = False,
        session: Session = None,
        **kwargs,
    ):
        self.creds = creds or {}
        self.default_params = default_params or {}
        self.dry_run = dry_run
        self.session = session or ClientSession(**kwargs)

        self._access_token = None
        self._token_expires = None

        # Controllers
        # TODO: Improve Sphinx docs generated for these attributes
        self.observations = ObservationController(self)  #: Interface for observation requests
        self.projects = ProjectController(self)  #: Interface for project requests
        self.taxa = TaxonController(self)  #: Interface for taxon requests

    @property
    def access_token(self):
        """Reuse an existing access token, if it's not expired; otherwise, get a new one"""
        if self._is_token_expired():
            logger.info('Access token expired, requesting a new one')
            self._access_token = get_access_token(**self.creds)
            self._token_expires = datetime.utcnow() + TOKEN_EXPIRATION
        else:
            logger.debug('Using active access token')
        return self._access_token

    def _is_token_expired(self):
        initialized = self._access_token and self._token_expires
        return not (initialized and datetime.utcnow() < self._token_expires)

    def request(
        self, request_function: Callable, *args, auth: bool = False, **params
    ) -> JsonResponse:
        """Apply any applicable client settings to request parameters before sending a request.
        Explicit keyword arguments will override any client settings.

        Args:
            request_function: The API request function to call, which should return a JSON response
            args: Any positional arguments to pass to the request function
            auth: Indicates that the request requires authentication
            params: Original request parameters
        """
        params = strip_empty_values(params)
        client_settings = {
            'dry_run': self.dry_run,
            'session': self.session,
        }

        # Add access token and default params, if applicable
        if auth:
            client_settings['access_token'] = self.access_token
        client_settings.update(get_valid_kwargs(request_function, self.default_params))

        for k, v in client_settings.items():
            params.setdefault(k, v)
        return request_function(*args, **params)
