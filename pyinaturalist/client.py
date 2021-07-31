# TODO: Use requests_cache.CachedSession by default?
# TODO: Create and refresh access tokens on demand (if using keyring)?
from logging import getLogger

from pyrate_limiter import Limiter
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from pyinaturalist import DEFAULT_USER_AGENT
from pyinaturalist.api_requests import RATE_LIMITER
from pyinaturalist.controllers import ObservationController

logger = getLogger(__name__)


# 'iNatClient' is nonstandard casing, but 'InatClient' just looks wrong. Deal with it, pep8.
class iNatClient:
    """**WIP** API Client class. See :py:mod:`.controller` documentation for request details.

    Examples:

        >>> # Basic usage:
        >>> from pyinaturalist import iNatClient
        >>> client = iNatClient()
        >>> observations = client.observations.search(taxon_name='Danaus plexippus')

        >>> # Custom rate-limiting settings: increase rate to 75 requests per minute:
        >>> from pyrate_limiter import Duration, Limiter, RequestRate
        >>> limiter = Limiter(RequestRate(75, Duration.MINUTE))
        >>> client = iNatClient(limiter=limiter)

        >>> # Custom retry settings: add longer delays, and only retry on 5xx errors:
        >>> from urllib3.util import Retry
        >>> Retry(total=10, backoff_factor=2, status_forcelist=[500, 501, 502, 503, 504])
        >>> client = iNatClient(retry=retry)

        >>> # All settings can be modified on an existing client object:
        >>> client.limiter = limiter
        >>> client.retry = retry
        >>> client.user_agent = 'My custom user agent'
        >>> client.dry_run = True

    Args:
        dry_run: Just log all requests instead of sending real requests
        limiter: Rate-limiting settings to use instead of the default
        retry: Retry settings to use instead of the default
        session: Session object to use instead of creating a new one
        user_agent: User-Agent string to pass to API requests
    """

    def __init__(
        self,
        dry_run: bool = False,
        limiter: Limiter = RATE_LIMITER,
        retry: Retry = None,
        session: Session = None,
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        self.access_token = None
        self.dry_run = dry_run
        self.limiter = limiter
        self.session = session or Session()
        self.retry = retry or Retry(total=5, backoff_factor=0.5)
        self.user_agent = user_agent

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
