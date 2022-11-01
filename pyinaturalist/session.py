"""Session class and related functions for preparing and sending API requests"""
import threading
from json import JSONDecodeError
from logging import getLogger
from os import getenv
from typing import Dict, Optional, Type
from unittest.mock import Mock

from requests import PreparedRequest, Request, Response, Session
from requests.adapters import HTTPAdapter
from requests.utils import default_user_agent
from requests_cache import CacheMixin, ExpirationPatterns, ExpirationTime
from requests_ratelimiter import (
    AbstractBucket,
    BucketFullException,
    Limiter,
    LimiterMixin,
    RequestRate,
    SQLiteBucket,
)
from urllib3.util import Retry

import pyinaturalist
from pyinaturalist.constants import (
    CACHE_EXPIRATION,
    CACHE_FILE,
    CONNECT_TIMEOUT,
    MAX_DELAY,
    RATELIMIT_FILE,
    REQUEST_BURST_RATE,
    REQUEST_RETRIES,
    REQUEST_TIMEOUT,
    REQUESTS_PER_DAY,
    REQUESTS_PER_MINUTE,
    REQUESTS_PER_SECOND,
    RETRY_BACKOFF,
    RETRY_STATUSES,
    WRITE_HTTP_METHODS,
    FileOrPath,
    MultiInt,
    RequestParams,
)
from pyinaturalist.converters import ensure_file_obj
from pyinaturalist.formatters import format_request, format_response
from pyinaturalist.request_params import (
    convert_url_ids,
    preprocess_request_body,
    preprocess_request_params,
)

# Mock response content to return in dry-run mode
MOCK_RESPONSE = Mock(spec=Response)
MOCK_RESPONSE.json.return_value = {'results': [], 'total_results': 0, 'access_token': ''}

# Rate limiter specific to forced refresh request
REFRESH_LIMITER = Limiter(
    RequestRate(1, 122),
    bucket_class=SQLiteBucket,
    bucket_kwargs={'path': RATELIMIT_FILE},
)

logger = getLogger('pyinaturalist')
thread_local = threading.local()


class ClientSession(CacheMixin, LimiterMixin, Session):
    """Custom session class used for sending API requests. Combines the following features and
    settings:

    * Caching
    * Rate-limiting (skipped for cached requests)
    * Retries
    * Timeouts
    """

    def __init__(
        self,
        cache_file: FileOrPath = CACHE_FILE,
        cache_control: bool = True,
        expire_after: Optional[ExpirationTime] = None,
        urls_expire_after: Optional[ExpirationPatterns] = None,
        per_second: int = REQUESTS_PER_SECOND,
        per_minute: int = REQUESTS_PER_MINUTE,
        per_day: float = REQUESTS_PER_DAY,
        burst: int = REQUEST_BURST_RATE,
        bucket_class: Type[AbstractBucket] = SQLiteBucket,
        backoff_factor: float = RETRY_BACKOFF,
        max_retries: int = REQUEST_RETRIES,
        timeout: int = REQUEST_TIMEOUT,
        user_agent: Optional[str] = None,
        **kwargs,
    ):
        """Get a Session object, optionally with custom settings for caching and rate-limiting.

        Args:
            cache_file: Cache file path to use; defaults to the system default cache directory
            cache_control: Use server-provided Cache-Control headers to set cache expiration when
                possible (instead of ``expire_after`` or ``urls_expire_after``)
            expire_after: How long to keep cached API requests; for advanced options, see
                `requests-cache: Expiration <https://requests-cache.readthedocs.io/en/latest/user_guide/expiration.html>`_
            urls_expire_after Glob patterns for per-URL cache expiration; See
                `requests-cache: URL Patterns <https://requests-cache.readthedocs.io/en/stable/user_guide/expiration.html#url-patterns>`_
            per_second: Max requests per second
            per_minute: Max requests per minute
            per_day: Max requests per day
            burst: Max number of consecutive requests allowed before applying per-second rate-limiting
            bucket_class: Rate-limiting backend to use. Defaults to a persistent SQLite database.
            backoff_factor: Factor for increasing delays between retries
            max_retries: Maximum number of times to retry a failed request
            timeout: Maximum number of seconds to wait for a response from the server
            user_agent: Additional User-Agent info to pass to API requests
            kwargs: Additional keyword arguments for :py:class:`~requests_cache.session.CachedSession`
                and/or :py:class:`~requests_ratelimiter.requests_ratelimiter.LimiterSession`
        """
        # Extend default URL expiration patterns with user-provided ones, if any
        url_patterns = CACHE_EXPIRATION
        if urls_expire_after:
            url_patterns.update(urls_expire_after)
        self.timeout = timeout

        super().__init__(  # type: ignore  # false positive
            # Cache settings
            cache_name=cache_file,
            backend='sqlite',
            cache_control=cache_control,
            expire_after=expire_after,
            urls_expire_after=url_patterns,
            ignored_parameters=['Authorization', 'access_token'],
            stale_if_error=True,
            # Rate limit settings
            bucket_class=bucket_class,
            bucket_kwargs={'path': RATELIMIT_FILE},
            per_second=per_second,
            per_minute=per_minute,
            per_day=per_day,
            per_host=True,
            burst=burst,
            max_delay=MAX_DELAY,
            **kwargs,
        )

        # Retry settings
        self.retries = Retry(
            total=max_retries, backoff_factor=backoff_factor, status_forcelist=RETRY_STATUSES
        )
        adapter = HTTPAdapter(max_retries=self.retries)
        self.mount('https://', adapter)

        # Default headers
        self.headers['Accept'] = 'application/json'
        user_agent_details = [
            default_user_agent(),
            f'pyinaturalist/{pyinaturalist.__version__}',
            user_agent or '',
        ]
        self.headers['User-Agent'] = ' '.join(user_agent_details).strip()

    def prepare_inat_request(
        self,
        method: str,
        url: str,
        access_token: Optional[str] = None,
        files: Optional[FileOrPath] = None,
        headers: Optional[Dict] = None,
        ids: Optional[MultiInt] = None,
        json: Optional[Dict] = None,
        params: Optional[RequestParams] = None,
        allow_str_ids: bool = False,
        **kwargs,
    ) -> PreparedRequest:
        """Translate pyinaturalist-specific options into standard request arguments"""
        # Prepare request params and URL
        params = preprocess_request_params(params)
        url = convert_url_ids(url, ids, allow_str_ids)

        # Set auth header
        headers = headers or {}
        if access_token:
            headers['Authorization'] = f'Bearer {access_token}'

        # Convert any datetimes in request body, and read any files or URLs for uploading
        json = preprocess_request_body(json)
        if files:
            files = {'file': ensure_file_obj(files, self)}  # type: ignore

        # Convert into a PreparedRequest
        request = Request(
            method=method,
            url=url,
            files=files,
            headers=headers,
            json=json,
            params=params,
            **kwargs,
        )
        return super().prepare_request(request)

    def request(  # type: ignore
        self,
        method: str,
        url: str,
        headers: Optional[Dict] = None,
        json: Optional[Dict] = None,
        access_token: Optional[str] = None,
        allow_redirects: bool = False,
        allow_str_ids: bool = False,
        dry_run: bool = False,
        expire_after: Optional[ExpirationTime] = None,
        files: Optional[FileOrPath] = None,
        ids: Optional[MultiInt] = None,
        only_if_cached: bool = False,
        raise_for_status: bool = True,
        refresh: bool = False,
        stream: bool = False,
        timeout: Optional[int] = None,
        verify: bool = True,
        **params: RequestParams,
    ) -> Response:
        """Wrapper around :py:func:`requests.request` with additional options specific to iNat API requests

        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            json: JSON request body
            access_token: access_token: the access token, as returned by :func:`get_access_token()`
            dry_run: Just log the request instead of sending a real request
            expire_after: How long to keep cached API requests
            files: File object, path, or URL to upload
            ids: One or more integer IDs used as REST resource(s) to request
            refresh: Skip reading from the cache and always fetch a fresh response
            timeout: Time (in seconds) to wait for a response from the server; if exceeded, a
                :py:exc:`requests.exceptions.Timeout` will be raised.
            params: All other keyword arguments will be used as request parameters

        Returns:
            API response
        """
        request = self.prepare_inat_request(
            method=method,
            url=url,
            access_token=access_token,
            allow_str_ids=allow_str_ids,
            files=files,
            headers=headers,
            ids=ids,
            json=json,
            params=params,
        )
        logger.info(format_request(request, dry_run))

        # Make a mock request, if specified
        if dry_run or is_dry_run_enabled(method):
            return MOCK_RESPONSE

        # Otherwise, send the request
        response = self.send(
            request,
            timeout=timeout,
            expire_after=expire_after,
            only_if_cached=only_if_cached,
            refresh=refresh,
            allow_redirects=allow_redirects,
            stream=stream,
            verify=verify,
        )
        logger.debug(format_response(response))

        # Raise an exception if the request failed (after retries are exceeded)
        if raise_for_status:
            response.raise_for_status()
        return response

    def send(  # type: ignore  # Adds kwargs not present in Session.send()
        self,
        request: PreparedRequest,
        expire_after: Optional[ExpirationTime] = None,
        refresh: bool = False,
        retries: Optional[Retry] = None,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> Response:
        """Send a request with caching, rate-limiting, and retries

        Args:
            request: Prepared request to send
            expire_after: How long to keep cached API requests
            refresh: Skip reading from the cache and always fetch a fresh response
            timeout: Maximum number of seconds to wait for a response from the server

        **Note:** :py:meth:`requests.Session.send` accepts separate timeout values for connect and
        read timeouts. The ``timeout`` argument will be used as the read timeout.
        """
        read_timeout = timeout or self.timeout
        response = super().send(
            request,
            expire_after=expire_after,
            refresh=refresh,
            timeout=(CONNECT_TIMEOUT, read_timeout),
            **kwargs,
        )
        response = self._validate_json(
            request,
            response,
            expire_after=expire_after,
            retries=retries,
            timeout=timeout,
            **kwargs,
        )
        return response

    def _validate_json(
        self,
        request: PreparedRequest,
        response: Response,
        retries: Optional[Retry] = None,
        **kwargs,
    ) -> Response:
        """Occasionally, the API may return invalid (truncated) JSON, requiring a retry. This method
        checks for this condition, treats it as a request error, and applies existing retry settings
        (so behavior is consistent with ``urllib3.ConnectionPool.urlopen()``).
        """
        # Skip for non-JSON responses
        if not response.headers.get('Content-Type', '').startswith('application/json'):
            return response

        # Attempt to decode the response content as JSON
        try:
            response_json = response.json()
        # Update retry state and wait before sending the request again
        except JSONDecodeError as e:
            logger.info('Invalid JSON response; retrying...')
            retries = retries or self.retries
            retries = retries.increment(
                response.request.method,
                response.request.url,
                error=e,
            )
            retries.sleep()
            kwargs['force_refresh'] = True
            kwargs['retries'] = retries
            return self.send(request, **kwargs)
        # Save decoded JSON on response object, to avoid decoding twice
        else:
            response.json = lambda **kwargs: response_json  # type: ignore
            return response


def delete(url: str, session: Optional[ClientSession] = None, **kwargs) -> Response:
    """Wrapper around :py:func:`requests.delete` with additional options specific to iNat API requests"""
    session = session or get_local_session()
    return session.request('DELETE', url, **kwargs)


def get(url: str, session: Optional[ClientSession] = None, **kwargs) -> Response:
    """Wrapper around :py:func:`requests.get` with additional options specific to iNat API requests"""
    session = session or get_local_session()
    return session.request('GET', url, **kwargs)


def post(url: str, session: Optional[ClientSession] = None, **kwargs) -> Response:
    """Wrapper around :py:func:`requests.post` with additional options specific to iNat API requests"""
    session = session or get_local_session()
    return session.request('POST', url, **kwargs)


def put(url: str, session: Optional[ClientSession] = None, **kwargs) -> Response:
    """Wrapper around :py:func:`requests.put` with additional options specific to iNat API requests"""
    session = session or get_local_session()
    return session.request('PUT', url, **kwargs)


def clear_cache():
    """Clear all cached API responses"""
    get_local_session().cache.clear()


def env_to_bool(environment_variable: str) -> bool:
    """Translate an environment variable to a boolean value, accounting for minor
    variations (case, None vs. False, etc.)
    """
    env_value = getenv(environment_variable)
    return bool(env_value) and str(env_value).lower() not in ['false', 'none']


def get_local_session(**kwargs) -> ClientSession:
    """Get a thread-local Session object with default settings. This will be reused across requests
    to take advantage of connection pooling and (optionally) caching. If used in a multi-threaded
    context (for example, a :py:class:`~concurrent.futures.ThreadPoolExecutor`), this will create
    and store a separate session object for each thread.

    Args:
        kwargs: Keyword arguments for :py:func:`.ClientSession`
    """
    if not hasattr(thread_local, 'session'):
        thread_local.session = ClientSession(**kwargs)
    return thread_local.session


def get_refresh_params(endpoint) -> Dict:
    """In some cases, we need to be sure we have the most recent version of a resource, for example
    when updating projects. Normally we would handle this with cache headers, but the CDN cache does
    not respect these if the cached response is less than ~2 minutes old.

    The iNat webapp handles this by adding an extra `v` request parameter, which results in a
    different cache key. This function does the same by tracking a separate rate limit per value,
    and finding the lowest value that is certain to result in a fresh response.
    """
    v = 0
    while True:
        try:
            bucket = f'{endpoint}?v={v}'
            REFRESH_LIMITER.try_acquire(bucket)
            break
        except BucketFullException as e:
            seconds = int(e.meta_info["remaining_time"])
            logger.debug(f'{bucket} cannot be refreshed again for {seconds} seconds')
            v += 1

    return {'refresh': True, 'v': v} if v > 0 else {'refresh': True}


def is_dry_run_enabled(method: str) -> bool:
    """A wrapper to determine if dry-run (aka test mode) has been enabled via either
    a constant or an environment variable. Dry-run mode may be enabled for either write
    requests, or all requests.
    """
    dry_run_enabled = env_to_bool('DRY_RUN_ENABLED')
    dry_run_write_only = env_to_bool('DRY_RUN_WRITE_ONLY') and method in WRITE_HTTP_METHODS
    return dry_run_enabled or dry_run_write_only
