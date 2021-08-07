# TODO: Use requests_cache.CachedSession by default
from datetime import datetime
from logging import getLogger
from typing import Any, Callable, Dict

from pyrate_limiter import Limiter
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from pyinaturalist import DEFAULT_USER_AGENT
from pyinaturalist.api_requests import RATE_LIMITER, get_session
from pyinaturalist.auth import get_access_token
from pyinaturalist.constants import MAX_RETRIES, TOKEN_EXPIRATION, JsonResponse
from pyinaturalist.controllers import ObservationController, ProjectController, TaxonController
from pyinaturalist.request_params import get_valid_kwargs, strip_empty_values

logger = getLogger(__name__)


# 'iNatClient' is nonstandard casing, but 'InatClient' just looks wrong. Deal with it, pep8.
class iNatClient:
    """**WIP/Experimental**

    API Client class. This provides a higher-level interface that is easier
    to configure, maintains some basic state information, and returns
    :ref:`model objects <models>` instead of JSON.
    See :ref:`Controller classes <controllers>` for request details.

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

        **Rate-limiting**

        Custom rate-limiting settings: increase rate to 75 requests per minute:

        >>> from pyrate_limiter import Duration, Limiter, RequestRate
        >>> limiter = Limiter(RequestRate(75, Duration.MINUTE))
        >>> client = iNatClient(limiter=limiter)

        **Retries**

        Custom retry settings: add longer delays, and only retry on 5xx errors:

        >>> from urllib3.util import Retry
        >>> Retry(total=10, backoff_factor=2, status_forcelist=[500, 501, 502, 503, 504])
        >>> client = iNatClient(retry=retry)

        **Caching**

        All API requests are cached by default. These expire in 1 hour for most endpoints, and
        longer for some infrequently-changing data (like taxa and places). To disable caching:

        >>> client = iNatClient(cache=False)

        Alternatively, you can use a :py:class:`~requests_cache.session.CachedSession` to customize
        cache settings. See the requests-cache
        `User Guide <https://requests-cache.readthedocs.io/en/stable/user_guide.html>`_
        for more details.

        >>> from datetime import timedelta
        >>> from requests_cache import CachedSession
        >>>
        >>> # Only cache requests for 15 minutes
        >>> session = CachedSession(
        ...     cache_name='api_requests.db',
        ...     expire_after=timedelta(minutes=15),
        ... )
        >>> client = iNatClient(session=session)
        >>>
        >>> # Or, cache requests without expiration
        >>> session = CachedSession(
        ...     cache_name='api_requests.db',
        ...     expire_after=-1,
        ... )
        >>> client = iNatClient(session=session)
        >>>
        >>> # Manually clear the cache
        >>> client.session.cache.clear()

        **Updating settings**

        All settings can also be modified after creating the client:

        >>> client.session = Session()
        >>> client.creds['username'] = 'my_inaturalist_username'
        >>> client.default_params['locale'] = 'es'
        >>> client.dry_run = True
        >>> client.limiter = limiter
        >>> client.retry = retry
        >>> client.user_agent = 'My custom user agent'

        .. note:: The ``cache`` and ``retry`` settings are stored on the session object, so updating
            ``client.session`` will override these settings as well.

    Args:
        cache: Cache API requests
        creds: Optional arguments for :py:func:`.get_access_token`, used to get and refresh access
            tokens as needed.
        default_params: Default request parameters to pass to any applicable API requests.
        dry_run: Just log all requests instead of sending real requests
        limiter: Rate-limiting settings to use instead of the default
        retry: Retry settings to use instead of the default
        session: Session object to use instead of creating a new one
        user_agent: User-Agent string to pass to API requests
    """

    def __init__(
        self,
        cache: bool = False,
        creds: Dict[str, str] = None,
        default_params: Dict[str, Any] = None,
        dry_run: bool = False,
        limiter: Limiter = RATE_LIMITER,
        retry: Retry = None,
        session: Session = None,
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        self.creds = creds or {}
        self.default_params = default_params or {}
        self.dry_run = dry_run
        self.limiter = limiter
        self.session = session or get_session(cache=cache)
        self.retry = retry or Retry(total=MAX_RETRIES, backoff_factor=0.5)
        self.user_agent = user_agent

        self._access_token = None
        self._token_expires = None

        # Controllers
        # TODO: Improve Sphinx docs generated for these attributes
        self.observations = ObservationController(self)  #: Interface for observation requests
        self.projects = ProjectController(self)  #: Interface for project requests
        self.taxa = TaxonController(self)  #: Interface for taxon requests

    @property
    def retry(self) -> Retry:
        """Get or modify retry settings via an adapter on the session"""
        adapter = self.session.adapters['https://']
        return adapter.max_retries

    @retry.setter
    def retry(self, value: Retry):
        """Add or update retry settings by mounting an adapter to the session"""
        adapter = HTTPAdapter(max_retries=value)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    @property
    def access_token(self):
        """Reuse an existing access token, if it's not expired; otherwise, get a new one"""
        if self._is_expired():
            logger.info('Access token expired, requesting a new one')
            self._access_token = get_access_token(**self.creds)
            self._token_expires = datetime.utcnow() + TOKEN_EXPIRATION
        else:
            logger.debug('Using active access token')
        return self._access_token

    @access_token.setter
    def access_token(self, value):
        self._access_token = value

    def _is_expired(self):
        initialized = self._access_token and self._token_expires
        return not (initialized and datetime.utcnow() < self._token_expires)

    def request(self, request_function: Callable, *args, auth: bool = False, **params) -> JsonResponse:
        """Apply any applicable client settings to request parameters before making the specified
        request. Explicit keyword arguments will override any client settings.

        Args:
            request_function: The API request function to call, which should return a JSON response
            args: Any positional arguments to pass to the request function
            auth: Indicates that the request requires authentication
            params: Original request parameters
        """
        params = strip_empty_values(params)
        client_settings = {
            'dry_run': self.dry_run,
            'limiter': self.limiter,
            'session': self.session,
            'user_agent': self.user_agent,
        }

        # Add access token and default params, if applicable
        if auth:
            client_settings['access_token'] = self.access_token
        client_settings.update(get_valid_kwargs(request_function, self.default_params))

        for k, v in client_settings.items():
            params.setdefault(k, v)
        return request_function(*args, **params)
