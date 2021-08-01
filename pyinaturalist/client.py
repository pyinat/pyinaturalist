# TODO: Use requests_cache.CachedSession by default
from datetime import datetime
from logging import getLogger
from typing import Dict

from pyrate_limiter import Limiter
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from pyinaturalist import DEFAULT_USER_AGENT
from pyinaturalist.api_requests import RATE_LIMITER
from pyinaturalist.auth import get_access_token
from pyinaturalist.constants import TOKEN_EXPIRATION
from pyinaturalist.controllers import ObservationController

logger = getLogger(__name__)


# 'iNatClient' is nonstandard casing, but 'InatClient' just looks wrong. Deal with it, pep8.
class iNatClient:
    """**WIP/Experimental** API Client class. This provides a higher-level interface that is easier
    to configure, maintains some basic state information, and returns
    :py:mod:`model objects <pyinaturalist.models>` instead of JSON.
    See :py:mod:`.controllers` documentation for request details.

    Examples:

        >>> # Basic usage:
        >>> from pyinaturalist import iNatClient
        >>> client = iNatClient()
        >>> observations = client.observations.search(taxon_name='Danaus plexippus')

        >>> # Add credentials needed for authenticated requests:
        >>> # Note: Passing credentials via environment variables or keyring is preferred
        >>> creds = {
        ...     'username': 'my_inaturalist_username',
        ...     'password': 'my_inaturalist_password',
        ...     'app_id': '33f27dc63bdf27f4ca6cd95dd9dcd5df',
        ...     'app_secret': 'bbce628be722bfe2abd5fc566ba83de4',
        ... }
        >>> client = iNatClient(creds=creds)

        >>> # Custom rate-limiting settings: increase rate to 75 requests per minute:
        >>> from pyrate_limiter import Duration, Limiter, RequestRate
        >>> limiter = Limiter(RequestRate(75, Duration.MINUTE))
        >>> client = iNatClient(limiter=limiter)

        >>> # Custom retry settings: add longer delays, and only retry on 5xx errors:
        >>> from urllib3.util import Retry
        >>> Retry(total=10, backoff_factor=2, status_forcelist=[500, 501, 502, 503, 504])
        >>> client = iNatClient(retry=retry)

        >>> # All settings can also be modified after creating the client object:
        >>> client.limiter = limiter
        >>> client.retry = retry
        >>> client.user_agent = 'My custom user agent'
        >>> client.dry_run = True

    Args:
        creds: Optional arguments for :py:func:`.get_access_token`, used to get and refresh access
            tokens as needed.
        dry_run: Just log all requests instead of sending real requests
        limiter: Rate-limiting settings to use instead of the default
        retry: Retry settings to use instead of the default
        session: Session object to use instead of creating a new one
        user_agent: User-Agent string to pass to API requests
    """

    def __init__(
        self,
        creds: Dict[str, str] = None,
        dry_run: bool = False,
        limiter: Limiter = RATE_LIMITER,
        retry: Retry = None,
        session: Session = None,
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        self.creds = creds or {}
        self.dry_run = dry_run
        self.limiter = limiter
        self.session = session or Session()
        self.retry = retry or Retry(total=5, backoff_factor=0.5)
        self.user_agent = user_agent

        self._access_token = None
        self._token_expires = None

        # Controllers
        self.observations = ObservationController(self)
        # self.taxa = TaxonController(self)
        # etc.

    @property
    def retry(self) -> Retry:
        """The current retry settings"""
        adapter = self.session.adapters['https://']
        return adapter.max_retries

    @retry.setter
    def retry(self, value: Retry):
        """Add or modify retry settings by mounting an adapter to the session"""
        adapter = HTTPAdapter(max_retries=value)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    @property
    def settings(self):
        """Get client settings to pass to an API request"""
        return {
            'dry_run': self.dry_run,
            'limiter': self.limiter,
            'session': self.session,
            'user_agent': self.user_agent,
        }

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
