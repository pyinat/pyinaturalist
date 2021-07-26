"""Some common functions for HTTP requests used by all API modules"""
# TODO: Default retry and backoff settings
import threading
from contextlib import contextmanager
from logging import getLogger
from os import getenv
from typing import Dict
from unittest.mock import Mock

from pyrate_limiter import Duration, Limiter, RequestRate
from requests import Response, Session

import pyinaturalist
from pyinaturalist.constants import (
    MAX_DELAY,
    REQUESTS_PER_DAY,
    REQUESTS_PER_MINUTE,
    REQUESTS_PER_SECOND,
    WRITE_HTTP_METHODS,
    MultiInt,
    RequestParams,
)
from pyinaturalist.docs import copy_signature
from pyinaturalist.request_params import prepare_request

# Default rate-limiting settings
RATE_LIMITER = Limiter(
    RequestRate(REQUESTS_PER_SECOND, Duration.SECOND),
    RequestRate(REQUESTS_PER_MINUTE, Duration.MINUTE),
    RequestRate(REQUESTS_PER_DAY, Duration.DAY),
)

# Mock response content to return in dry-run mode
MOCK_RESPONSE = Mock(spec=Response)
MOCK_RESPONSE.json.return_value = {'results': [], 'total_results': 0, 'access_token': ''}

logger = getLogger(__name__)
thread_local = threading.local()


def request(
    method: str,
    url: str,
    access_token: str = None,
    dry_run: bool = False,
    headers: Dict = None,
    ids: MultiInt = None,
    json: Dict = None,
    limiter: Limiter = None,
    session: Session = None,
    raise_for_status: bool = True,
    timeout: float = 5,
    user_agent: str = None,
    **params: RequestParams,
) -> Response:
    """Wrapper around :py:func:`requests.request` with additional options specific to iNat API requests

    Args:
        method: HTTP method
        url: Request URL
        access_token: access_token: the access token, as returned by :func:`get_access_token()`
        dry_run: Just log the request instead of sending a real request
        ids: One or more integer IDs used as REST resource(s) to request
        headers: Request headers
        json: JSON request body
        limiter: Custom rate limits to apply to this request
        session: An existing Session object to use instead of creating a new one
        timeout: Time (in seconds) to wait for a response from the server; if exceeded, a
            :py:exc:`requests.exceptions.Timeout` will be raised.
        user_agent: A custom user-agent string to provide to the iNaturalist API
        params: All other keyword arguments are interpreted as request parameters

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
    limiter = limiter or RATE_LIMITER
    session = session or get_session()

    # Run either real request or mock request depending on settings
    if dry_run or is_dry_run_enabled(method):
        logger.debug('Dry-run mode enabled; mocking request')
        log_request(method, url, params=params, headers=headers)
        return MOCK_RESPONSE
    else:
        with ratelimit():
            response = session.request(
                method, url, params=params, headers=headers, json=json, timeout=timeout
            )
        if raise_for_status:
            response.raise_for_status()
        return response


@copy_signature(request, exclude='method')
def delete(url: str, **kwargs) -> Response:
    """Wrapper around :py:func:`requests.delete` with additional options specific to iNat API requests"""
    return request('DELETE', url, **kwargs)


@copy_signature(request, exclude='method')
def get(url: str, **kwargs) -> Response:
    """Wrapper around :py:func:`requests.get` with additional options specific to iNat API requests"""
    return request('GET', url, **kwargs)


@copy_signature(request, exclude='method')
def post(url: str, **kwargs) -> Response:
    """Wrapper around :py:func:`requests.post` with additional options specific to iNat API requests"""
    return request('POST', url, **kwargs)


@copy_signature(request, exclude='method')
def put(url: str, **kwargs) -> Response:
    """Wrapper around :py:func:`requests.put` with additional options specific to iNat API requests"""
    return request('PUT', url, **kwargs)


# TODO: Handle error 429 if we still somehow exceed the rate limit?
@contextmanager
def ratelimit(bucket=pyinaturalist.user_agent):
    """Add delays in between requests to stay within the rate limits. If pyrate-limiter is
    not installed, this will quietly do nothing.
    """
    if RATE_LIMITER:
        with RATE_LIMITER.ratelimit(bucket, delay=True, max_delay=MAX_DELAY):
            yield
    else:
        yield


def get_session() -> Session:
    """Get a Session object that will be reused across requests to take advantage of connection
    pooling. This is especially relevant for large paginated requests. If used in a multi-threaded
    context (for example, a :py:class:`~concurrent.futures.ThreadPoolExecutor`), a separate session
    is used for each thread.
    """
    if not hasattr(thread_local, "session"):
        thread_local.session = Session()
    return thread_local.session


def is_dry_run_enabled(method: str) -> bool:
    """A wrapper to determine if dry-run (aka test mode) has been enabled via either
    a constant or an environment variable. Dry-run mode may be enabled for either write
    requests, or all requests.
    """
    dry_run_enabled = pyinaturalist.DRY_RUN_ENABLED or env_to_bool('DRY_RUN_ENABLED')
    if method in WRITE_HTTP_METHODS:
        return dry_run_enabled or pyinaturalist.DRY_RUN_WRITE_ONLY or env_to_bool('DRY_RUN_WRITE_ONLY')
    return dry_run_enabled


def env_to_bool(environment_variable: str) -> bool:
    """Translate an environment variable to a boolean value, accounting for minor
    variations (case, None vs. False, etc.)
    """
    env_value = getenv(environment_variable)
    return bool(env_value) and str(env_value).lower() not in ['false', 'none']


def log_request(*args, **kwargs):
    """Log all relevant information about an HTTP request"""
    kwargs_strs = [f'{k}={v}' for k, v in kwargs.items()]
    logger.info('Request: {}'.format(', '.join(list(args) + kwargs_strs)))
