"""Session class and related functions for preparing and sending API requests"""
import threading
from logging import getLogger
from os import getenv
from typing import Dict, List
from unittest.mock import Mock
from warnings import warn

import forge
from pyrate_limiter import Duration, RequestRate
from requests import PreparedRequest, Request, Response, Session
from requests.adapters import HTTPAdapter
from requests_cache import CacheMixin, ExpirationTime
from requests_ratelimiter import LimiterMixin
from urllib3.util import Retry

import pyinaturalist
from pyinaturalist.constants import (
    CACHE_EXPIRATION,
    CACHE_FILE,
    MAX_DELAY,
    MAX_RETRIES,
    REQUEST_BURST_RATE,
    REQUEST_TIMEOUT,
    REQUESTS_PER_DAY,
    REQUESTS_PER_MINUTE,
    REQUESTS_PER_SECOND,
    WRITE_HTTP_METHODS,
    FileOrPath,
    MultiInt,
    RequestParams,
)
from pyinaturalist.converters import ensure_file_obj
from pyinaturalist.formatters import format_request
from pyinaturalist.request_params import (
    convert_url_ids,
    preprocess_request_body,
    preprocess_request_params,
)

# Mock response content to return in dry-run mode
MOCK_RESPONSE = Mock(spec=Response)
MOCK_RESPONSE.json.return_value = {'results': [], 'total_results': 0, 'access_token': ''}

logger = getLogger('pyinaturalist')
thread_local = threading.local()


class iNatSession(CacheMixin, LimiterMixin, Session):  # type: ignore  # false positive
    """Custom session class used for sending API requests. Combines the following features:

    * Caching
    * Rate-limiting (skipped for cached requests)
    * Retries
    * Timeouts

    This is the default and recommended session class to use for API requests, but can be safely
    replaced with any :py:class:`~requests.session.Session`-compatible class via the ``session``
    argument for API request functions.
    """

    def __init__(
        self,
        expire_after: ExpirationTime = None,
        per_second: int = REQUESTS_PER_SECOND,
        per_minute: int = REQUESTS_PER_MINUTE,
        per_day: float = REQUESTS_PER_DAY,
        burst: int = REQUEST_BURST_RATE,
        retries: int = MAX_RETRIES,
        backoff_factor: float = 0.5,
        timeout: int = 10,
        **kwargs,
    ):
        """Get a Session object, optionally with custom settings for caching and rate-limiting.

        Args:
            expire_after: How long to keep cached API requests; for advanced options, see
                `requests-cache: Expiration <https://requests-cache.readthedocs.io/en/latest/user_guide/expiration.html>`_
            per_second: Max requests per second
            per_minute: Max requests per minute
            per_minute: Max requests per day
            burst: Max number of consecutive requests allowed before applying per-second rate-limiting
            retries: Maximum number of times to retry a failed request
            backoff_factor: Factor for increasing delays between retries
            timeout: Maximum number of seconds to wait for a response from the server
            kwargs: Additional keyword arguments for :py:class:`~requests_cache.session.CachedSession`
                and/or :py:class:`~requests_ratelimiter.requests_ratelimiter.LimiterSession`
        """
        # If not overridden, use default expiration times per API endpoint
        if not expire_after:
            kwargs.setdefault('urls_expire_after', CACHE_EXPIRATION)
        self.timeout = timeout

        # Initialize with caching and rate-limiting settings
        super().__init__(
            cache_name=CACHE_FILE,
            backend='sqlite',
            expire_after=expire_after,
            ignored_parameters=['access_token'],
            old_data_on_error=True,
            per_second=per_second,
            per_minute=per_minute,
            per_day=per_day,
            burst=burst,
            max_delay=MAX_DELAY,
            **kwargs,
        )

        # Mount an adapter to apply retry settings
        retry = Retry(total=retries, backoff_factor=backoff_factor)
        adapter = HTTPAdapter(max_retries=retry)
        self.mount('https://', adapter)

    def send(self, request: PreparedRequest, **kwargs) -> Response:  # type: ignore  # false positive
        """Send a request with caching, rate-limiting, and retries"""
        kwargs.setdefault('timeout', self.timeout)
        return super().send(request, **kwargs)


def request(
    method: str,
    url: str,
    access_token: str = None,
    dry_run: bool = False,
    files: FileOrPath = None,
    headers: Dict = None,
    ids: MultiInt = None,
    json: Dict = None,
    raise_for_status: bool = True,
    session: Session = None,
    timeout: float = REQUEST_TIMEOUT,
    user_agent: str = None,
    **params: RequestParams,
) -> Response:
    """Wrapper around :py:func:`requests.request` with additional options specific to iNat API requests

    Args:
        method: HTTP method
        url: Request URL
        access_token: access_token: the access token, as returned by :func:`get_access_token()`
        dry_run: Just log the request instead of sending a real request
        files: File path or object to upload
        headers: Request headers
        ids: One or more integer IDs used as REST resource(s) to request
        json: JSON request body
        session: An existing Session object to use instead of creating a new one
        timeout: Time (in seconds) to wait for a response from the server; if exceeded, a
            :py:exc:`requests.exceptions.Timeout` will be raised.
        user_agent: A custom user-agent string to provide to the iNaturalist API
        params: All other keyword arguments are interpreted as request parameters

    Returns:
        API response
    """
    session = session or get_local_session()
    request = prepare_request(
        method=method,
        url=url,
        access_token=access_token,
        files=files,
        headers=headers,
        ids=ids,
        json=json,
        params=params,
        user_agent=user_agent,
    )
    logger.info(format_request(request, dry_run))

    # Make a mock request, if specified
    if dry_run or is_dry_run_enabled(method):
        return MOCK_RESPONSE

    # Otherwise, send the request
    response = session.send(request, timeout=timeout)
    if raise_for_status:
        response.raise_for_status()
    return response


def prepare_request(
    method: str,
    url: str,
    access_token: str = None,
    files: FileOrPath = None,
    headers: Dict = None,
    ids: MultiInt = None,
    json: Dict = None,
    params: RequestParams = None,
    user_agent: str = None,
    **kwargs,
) -> PreparedRequest:
    """Translate ``pyinaturalist``-specific options into standard request arguments"""
    # Prepare request params and URL
    params = preprocess_request_params(params)
    url = convert_url_ids(url, ids)

    # Prepare user-agent and authentication headers
    headers = headers or {}
    headers['User-Agent'] = user_agent or pyinaturalist.user_agent
    headers['Accept'] = 'application/json'
    if access_token:
        headers['Authorization'] = f'Bearer {access_token}'

    # Convert any datetimes to strings in request body
    if json:
        headers['Content-type'] = 'application/json'
        json = preprocess_request_body(json)

    # Read any files for uploading
    if files:
        files = {'file': ensure_file_obj(files)}  # type: ignore

    request = Request(
        method=method, url=url, files=files, headers=headers, json=json, params=params, **kwargs
    )
    return request.prepare()


@forge.copy(request, exclude='method')
def delete(url: str, **kwargs) -> Response:
    """Wrapper around :py:func:`requests.delete` with additional options specific to iNat API requests"""
    return request('DELETE', url, **kwargs)


@forge.copy(request, exclude='method')
def get(url: str, **kwargs) -> Response:
    """Wrapper around :py:func:`requests.get` with additional options specific to iNat API requests"""
    return request('GET', url, **kwargs)


@forge.copy(request, exclude='method')
def post(url: str, **kwargs) -> Response:
    """Wrapper around :py:func:`requests.post` with additional options specific to iNat API requests"""
    return request('POST', url, **kwargs)


@forge.copy(request, exclude='method')
def put(url: str, **kwargs) -> Response:
    """Wrapper around :py:func:`requests.put` with additional options specific to iNat API requests"""
    return request('PUT', url, **kwargs)


def env_to_bool(environment_variable: str) -> bool:
    """Translate an environment variable to a boolean value, accounting for minor
    variations (case, None vs. False, etc.)
    """
    env_value = getenv(environment_variable)
    return bool(env_value) and str(env_value).lower() not in ['false', 'none']


# TODO: Drop support for global variables in version 0.16
def is_dry_run_enabled(method: str) -> bool:
    """A wrapper to determine if dry-run (aka test mode) has been enabled via either
    a constant or an environment variable. Dry-run mode may be enabled for either write
    requests, or all requests.
    """
    if pyinaturalist.DRY_RUN_ENABLED or pyinaturalist.DRY_RUN_WRITE_ONLY:
        msg = (
            'Global varibale usage is deprecated; please use environment variables or dry_run '
            'keyword argument instead'
        )
        warn(DeprecationWarning(msg))

    dry_run_enabled = pyinaturalist.DRY_RUN_ENABLED or env_to_bool('DRY_RUN_ENABLED')
    if method in WRITE_HTTP_METHODS:
        return dry_run_enabled or pyinaturalist.DRY_RUN_WRITE_ONLY or env_to_bool('DRY_RUN_WRITE_ONLY')
    return dry_run_enabled


def get_local_session(**kwargs) -> Session:
    """Get a thread-local Session object with default settings. This will be reused across requests
    to take advantage of connection pooling and (optionally) caching. If used in a multi-threaded
    context (for example, a :py:class:`~concurrent.futures.ThreadPoolExecutor`), this will create
    and store a separate session object for each thread.

    Args:
        kwargs: Keyword arguments for :py:func:`.iNatSession`
    """
    if not hasattr(thread_local, 'session'):
        thread_local.session = iNatSession(**kwargs)
    return thread_local.session


def get_request_rates(per_second: int, per_minute: int, burst: int) -> List[RequestRate]:
    """Translate request rate values into RequestRate objects"""
    return [
        RequestRate(per_second * burst, Duration.SECOND * burst),
        RequestRate(per_minute, Duration.MINUTE),
        RequestRate(REQUESTS_PER_DAY, Duration.DAY),
    ]
