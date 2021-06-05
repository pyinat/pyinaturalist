"""TODO:
Lots of details to figure out here. Should this use features from api_requests.py and other modules,
or the other way around? Are they better as static functions or instance methods?
Currently leaning towards the latter.

Main features include:
* Pagination
* Rate-limiting
* Caching (with #158)
* Dry-run mode
* Thread-local session factory
"""
import threading
from contextlib import contextmanager
from datetime import date, datetime
from logging import getLogger
from typing import Dict, Optional, Tuple
from unittest.mock import Mock

from pyrate_limiter import Duration, Limiter, RequestRate
from requests import Response, Session

from pyinaturalist import DEFAULT_USER_AGENT
from pyinaturalist.constants import (
    MAX_DELAY,
    REQUESTS_PER_DAY,
    REQUESTS_PER_MINUTE,
    REQUESTS_PER_SECOND,
    WRITE_HTTP_METHODS,
    MultiInt,
    RequestParams,
)
from pyinaturalist.controllers import ObservationController
from pyinaturalist.forge_utils import copy_signature
from pyinaturalist.request_params import prepare_request, preprocess_request_params, validate_ids

# Mock response content to return in dry-run mode
MOCK_RESPONSE = Mock(spec=Response)
MOCK_RESPONSE.json.return_value = {'results': [], 'total_results': 0, 'access_token': ''}

# Default rate-limiting settings
REQUEST_RATES = [
    RequestRate(REQUESTS_PER_SECOND, Duration.SECOND),
    RequestRate(REQUESTS_PER_MINUTE, Duration.MINUTE),
    RequestRate(REQUESTS_PER_DAY, Duration.DAY),
]
RATE_LIMITER = Limiter(*REQUEST_RATES)

logger = getLogger(__name__)


class iNatClient:
    """API Client class.
    'iNatClient' is nonstandard casing, but 'InatClient' just looks wrong. Deal with it, pep8.

    Args:
        dry_run: Mock and log all requests
        dry_run_write_only: Mock and log POST, PUT, and DELETE requests
        limiter: Rate-limiting settings to use instead of the default
        session: Session object to use instead of creating a new one
        user_agent: User-Agent string to pass to API requests
    """

    def __init__(
        self,
        dry_run: bool = False,
        dry_run_write_only: bool = False,
        limiter: Limiter = RATE_LIMITER,
        session: Session = None,
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        self.access_token = None  # TODO: Create and refresh access tokens on demand (if using keyring)
        self.dry_run = dry_run
        self.dry_run_write_only = dry_run_write_only
        self.limiter = limiter
        self.local_ctx = threading.local()
        self.session = session  # TODO: requests_cache.CachedSession options
        self.user_agent = user_agent

        # Controllers
        self.observations = ObservationController(self)
        # self.taxa = TaxonController(self)
        # etc.

    def _is_dry_run_enabled(self, method: str) -> bool:
        """Determine if dry-run (aka test mode) has been enabled"""
        return self.dry_run or (self.dry_run_write_only and method in WRITE_HTTP_METHODS)

    def prepare_request(
        self,
        url: str,
        access_token: str = None,
        ids: MultiInt = None,
        params: RequestParams = None,
        headers: Dict = None,
        json: Dict = None,
    ) -> Tuple[str, RequestParams, Dict, Optional[Dict]]:
        """Translate some ``pyinaturalist``-specific params into standard request params, headers,
        and body. This is made non-``requests``-specific so it could potentially be reused for
        use with other HTTP clients.

        Returns:
            Tuple of ``(URL, params, headers, body)``
        """
        # Prepare request params
        params = preprocess_request_params(params)
        json = preprocess_request_params(json)

        # Prepare user and authentication headers
        headers = headers or {}
        headers['Accept'] = 'application/json'
        headers['User-Agent'] = params.pop('user_agent', self.user_agent)
        if access_token:
            headers['Authorization'] = f'Bearer {access_token}'
        if json:
            headers['Content-type'] = 'application/json'

        # If one or more resources are requested by ID, valudate and update the request URL accordingly
        if ids:
            url = url.rstrip('/') + '/' + validate_ids(ids)
        return url, params, headers, json

    # TODO: Handle error 429 if we still somehow exceed the rate limit?
    @contextmanager
    def ratelimit(self, bucket: str = None):
        """Add delays in between requests to stay within the rate limits"""
        if self.limiter:
            with self.limiter.ratelimit(bucket or self.user_agent, delay=True, max_delay=MAX_DELAY):
                yield
        else:
            yield

    def request(
        self,
        method: str,
        url: str,
        access_token: str = None,
        user_agent: str = None,
        ids: MultiInt = None,
        params: RequestParams = None,
        headers: Dict = None,
        json: Dict = None,
        session: Session = None,
        raise_for_status: bool = True,
        **kwargs,
    ) -> Response:
        """Wrapper around :py:func:`requests.request` that supports dry-run mode and rate-limiting,
        and adds appropriate headers.

        Args:
            method: HTTP method
            url: Request URL
            access_token: access_token: the access token, as returned by :func:`get_access_token()`
            user_agent: a user-agent string that will be passed to iNaturalist
            ids: One or more integer IDs used as REST resource(s) to request
            params: Requests parameters
            headers: Request headers
            json: JSON request body
            session: Existing Session object to use instead of creating a new one
            kwargs: Additional keyword arguments for :py:meth:`requests.Session.request`

        Returns:
            API response
        """
        url, params, headers, json = prepare_request(
            url,
            access_token,
            user_agent,
            ids,
            params,
            headers,
            json,
        )

        # Run either real request or mock request depending on settings
        if self._is_dry_run_enabled(method):
            log_request(method, url, params=params, headers=headers, **kwargs)
            return MOCK_RESPONSE
        else:
            with self.ratelimit():
                response = self.session.request(
                    method, url, params=params, headers=headers, json=json, **kwargs
                )
            if raise_for_status:
                response.raise_for_status()
            return response

    # @copy_signature(iNatClient.request, exclude='method')
    def delete(self, url: str, **kwargs) -> Response:
        """Wrapper around :py:func:`requests.delete` that supports dry-run mode and rate-limiting"""
        return self.request('DELETE', url, **kwargs)

    # @copy_signature(iNatClient.request, exclude='method')
    def get(self, url: str, **kwargs) -> Response:
        """Wrapper around :py:func:`requests.get` that supports dry-run mode and rate-limiting"""
        return self.request('GET', url, **kwargs)

    # @copy_signature(iNatClient.request, exclude='method')
    def post(self, url: str, **kwargs) -> Response:
        """Wrapper around :py:func:`requests.post` that supports dry-run mode and rate-limiting"""
        return self.request('POST', url, **kwargs)

    # @copy_signature(iNatClient.request, exclude='method')
    def put(self, url: str, **kwargs) -> Response:
        """Wrapper around :py:func:`requests.put` that supports dry-run mode and rate-limiting"""
        return self.request('PUT', url, **kwargs)

    @property
    def session(self) -> Session:
        """Get a Session object that will be reused across requests to take advantage of connection
        pooling. If used in a multi-threaded context (for example, a
        :py:class:`~concurrent.futures.ThreadPoolExecutor`), a separate session is used per thread.
        """
        if not hasattr(self.local_ctx, "session"):
            self.local_ctx.session = Session()
        return self.local_ctx.session

    @session.setter
    def session(self, session: Session):
        self.local_ctx.session = session


def log_request(*args, **kwargs):
    """Log all relevant information about an HTTP request"""
    kwargs_strs = [f'{k}={v}' for k, v in kwargs.items()]
    logger.info('Request: {}'.format(', '.join(list(args) + kwargs_strs)))
