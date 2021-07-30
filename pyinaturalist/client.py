# TODO: Use requests_cache.CachedSession by default?
# TODO: Create and refresh access tokens on demand (if using keyring)?
from logging import getLogger

from pyrate_limiter import Limiter
from requests import Session

from pyinaturalist import DEFAULT_USER_AGENT
from pyinaturalist.api_requests import RATE_LIMITER
from pyinaturalist.controllers import ObservationController

logger = getLogger(__name__)


class iNatClient:
    """API Client class.
    'iNatClient' is nonstandard casing, but 'InatClient' just looks wrong. Deal with it, pep8.

    Args:
        dry_run: Just log all requests instead of sending real requests
        limiter: Rate-limiting settings to use instead of the default
        session: Session object to use instead of creating a new one
        user_agent: User-Agent string to pass to API requests
    """

    def __init__(
        self,
        dry_run: bool = False,
        limiter: Limiter = RATE_LIMITER,
        session: Session = None,
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        self.access_token = None
        self.dry_run = dry_run
        self.limiter = limiter
        self.session = session or Session()
        self.user_agent = user_agent

        # Controllers
        self.observations = ObservationController(self)
        # self.taxa = TaxonController(self)
        # etc.

    @property
    def settings(self):
        """Get client settings to pass to an API request"""
        return {
            'dry_run': self.dry_run,
            'limiter': self.limiter,
            'session': self.session,
            'user_agent': self.user_agent,
        }
