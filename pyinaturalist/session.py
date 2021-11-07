"""Session class and related functions for preparing and sending API requests"""
import re
import threading
from io import BytesIO
from logging import getLogger
from os import getenv
from os.path import abspath, expanduser
from pathlib import Path
from typing import IO, Dict
from unittest.mock import Mock
from warnings import warn

import forge
from requests import PreparedRequest, Request, Response, Session
from requests.adapters import HTTPAdapter
from requests.utils import default_user_agent
from requests_cache import CacheMixin, ExpirationTime
from requests_ratelimiter import LimiterMixin
from urllib3.util import Retry

import pyinaturalist
from pyinaturalist.constants import (
    CACHE_EXPIRATION,
    CACHE_FILE,
    MAX_DELAY,
    REQUEST_BURST_RATE,
    REQUEST_RETRIES,
    REQUEST_TIMEOUT,
    REQUESTS_PER_DAY,
    REQUESTS_PER_MINUTE,
    REQUESTS_PER_SECOND,
    RETRY_BACKOFF,
    WRITE_HTTP_METHODS,
    AnyFile,
    FileOrPath,
    MultiInt,
    RequestParams,
)
from pyinaturalist.formatters import format_request
from pyinaturalist.request_params import (
    convert_url_ids,
    preprocess_request_body,
    preprocess_request_params,
)

# Mock response content to return in dry-run mode
MOCK_RESPONSE = Mock(spec=Response)
MOCK_RESPONSE.json.return_value = {'results': [], 'total_results': 0, 'access_token': ''}

# Extremely simplified URL regex, just enough to differentiate from local paths
URL_PATTERN = re.compile(r'^https?://.+')

logger = getLogger('pyinaturalist')
thread_local = threading.local()


class ClientSession(CacheMixin, LimiterMixin, Session):
    """Custom session class used for sending API requests. Combines the following features and
    settings:

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
        cache_file: FileOrPath = CACHE_FILE,
        per_second: int = REQUESTS_PER_SECOND,
        per_minute: int = REQUESTS_PER_MINUTE,
        per_day: float = REQUESTS_PER_DAY,
        burst: int = REQUEST_BURST_RATE,
        retries: int = REQUEST_RETRIES,
        backoff_factor: float = RETRY_BACKOFF,
        timeout: int = REQUEST_TIMEOUT,
        user_agent: str = None,
        **kwargs,
    ):
        """Get a Session object, optionally with custom settings for caching and rate-limiting.

        Args:
            expire_after: How long to keep cached API requests; for advanced options, see
                `requests-cache: Expiration <https://requests-cache.readthedocs.io/en/latest/user_guide/expiration.html>`_
            cache_file: Cache file path to use; defaults to the system default cache directory
            per_second: Max requests per second
            per_minute: Max requests per minute
            per_day: Max requests per day
            burst: Max number of consecutive requests allowed before applying per-second rate-limiting
            retries: Maximum number of times to retry a failed request
            backoff_factor: Factor for increasing delays between retries
            timeout: Maximum number of seconds to wait for a response from the server
            user_agent: Additional User-Agent info to pass to API requests
            kwargs: Additional keyword arguments for :py:class:`~requests_cache.session.CachedSession`
                and/or :py:class:`~requests_ratelimiter.requests_ratelimiter.LimiterSession`
        """
        # If not overridden, use Cache-Control when possible, and some default expiration times
        if not expire_after:
            kwargs.setdefault('cache_control', True)
            kwargs.setdefault('urls_expire_after', CACHE_EXPIRATION)
        self.timeout = timeout

        # Initialize with caching and rate-limiting settings
        super().__init__(  # type: ignore  # false positive
            cache_name=cache_file,
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

        # Set default headers
        self.headers['Accept'] = 'application/json'
        user_agent_details = [
            default_user_agent(),
            f'pyinaturalist/{pyinaturalist.__version__}',
            user_agent or '',
        ]
        self.headers['User-Agent'] = ' '.join(user_agent_details).strip()

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
    **params: RequestParams,
) -> Response:
    """Wrapper around :py:func:`requests.request` with additional options specific to iNat API requests

    Args:
        method: HTTP method
        url: Request URL
        access_token: access_token: the access token, as returned by :func:`get_access_token()`
        dry_run: Just log the request instead of sending a real request
        files: File object, path, or URL to upload
        headers: Request headers
        ids: One or more integer IDs used as REST resource(s) to request
        json: JSON request body
        session: An existing Session object to use instead of creating a new one
        timeout: Time (in seconds) to wait for a response from the server; if exceeded, a
            :py:exc:`requests.exceptions.Timeout` will be raised.
        params: All other keyword arguments are interpreted as request parameters

    Returns:
        API response
    """
    session = session or get_local_session()
    request = prepare_request(
        session=session,
        method=method,
        url=url,
        access_token=access_token,
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
    response = session.send(request)
    if raise_for_status:
        response.raise_for_status()
    return response


def prepare_request(
    session: Session,
    method: str,
    url: str,
    access_token: str = None,
    files: FileOrPath = None,
    headers: Dict = None,
    ids: MultiInt = None,
    json: Dict = None,
    params: RequestParams = None,
    **kwargs,
) -> PreparedRequest:
    """Translate ``pyinaturalist``-specific options into standard request arguments"""
    # Prepare request params and URL
    params = preprocess_request_params(params)
    url = convert_url_ids(url, ids)

    # Set auth header
    headers = headers or {}
    if access_token:
        headers['Authorization'] = f'Bearer {access_token}'

    # Convert any datetimes in request body, and read any files or URLs for uploading
    json = preprocess_request_body(json)
    if files:
        files = {'file': ensure_file_obj(files, session)}  # type: ignore

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
    return session.prepare_request(request)


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


def ensure_file_obj(value: AnyFile, session: Session = None) -> IO:
    """Given a file path or URL, load data into a file-like object"""
    # Load from URL
    if isinstance(value, str) and URL_PATTERN.match(value):
        session = session or get_local_session()
        return session.get(value).raw

    # Load from local file path
    if isinstance(value, (str, Path)):
        file_path = abspath(expanduser(value))
        logger.info(f'Reading from file: {file_path}')
        with open(file_path, 'rb') as f:
            return BytesIO(f.read())

    # Otherwise, assume it's already a file or file-like object
    return value


def env_to_bool(environment_variable: str) -> bool:
    """Translate an environment variable to a boolean value, accounting for minor
    variations (case, None vs. False, etc.)
    """
    env_value = getenv(environment_variable)
    return bool(env_value) and str(env_value).lower() not in ['false', 'none']


def get_local_session(**kwargs) -> Session:
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
        return (
            dry_run_enabled or pyinaturalist.DRY_RUN_WRITE_ONLY or env_to_bool('DRY_RUN_WRITE_ONLY')
        )
    return dry_run_enabled
