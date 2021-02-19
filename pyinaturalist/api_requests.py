""" Some common functions for HTTP requests used by both the Node and REST API modules """
import threading
from contextlib import contextmanager
from logging import getLogger
from os import getenv
from time import sleep
from typing import Dict, List, Union
from unittest.mock import Mock

import requests

import pyinaturalist
from pyinaturalist.constants import WRITE_HTTP_METHODS
from pyinaturalist.forge_utils import copy_signature
from pyinaturalist.request_params import preprocess_request_params, validate_ids

# Mock response content to return in dry-run mode
MOCK_RESPONSE = Mock(spec=requests.Response)
MOCK_RESPONSE.json.return_value = {'results': [], 'total_results': 0}

# Request rate limits. Only compatible with python 3.7+.
try:
    from pyrate_limiter import BucketFullException, Duration, Limiter, RequestRate

    REQUEST_RATES = [
        RequestRate(5, Duration.SECOND),
        RequestRate(60, Duration.MINUTE),
        RequestRate(10000, Duration.DAY),
    ]
    RATE_LIMITER = Limiter(*REQUEST_RATES)
except ImportError:
    RATE_LIMITER = None

MAX_RETRIES = 15

logger = getLogger(__name__)
thread_local = threading.local()


def request(
    method: str,
    url: str,
    access_token: str = None,
    user_agent: str = None,
    ids: Union[str, List] = None,
    params: Dict = None,
    headers: Dict = None,
    session: requests.Session = None,
    **kwargs,
) -> requests.Response:
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
        session: Existing Session object to use instead of creating a new one

    Returns:
        API response
    """
    # Set user agent and authentication headers, if specified
    session = session or get_session()
    headers = headers or {}
    headers['Accept'] = 'application/json'
    headers['User-Agent'] = user_agent or pyinaturalist.user_agent
    if access_token:
        headers['Authorization'] = f'Bearer {access_token}'

    params = preprocess_request_params(params)

    # If one or more REST resources are requested by ID, update the request URL accordingly
    if ids:
        url = url.rstrip('/') + '/' + validate_ids(ids)

    # Run either real request or mock request depending on settings
    if is_dry_run_enabled(method):
        logger.debug('Dry-run mode enabled; mocking request')
        log_request(method, url, params=params, headers=headers, **kwargs)
        return MOCK_RESPONSE
    else:
        with apply_rate_limit():
            return session.request(method, url, params=params, headers=headers, **kwargs)


@copy_signature(request, exclude='method')
def delete(url: str, **kwargs) -> requests.Response:
    """Wrapper around :py:func:`requests.delete` that supports dry-run mode and rate-limiting"""
    return request('DELETE', url, **kwargs)


@copy_signature(request, exclude='method')
def get(url: str, **kwargs) -> requests.Response:
    """Wrapper around :py:func:`requests.get` that supports dry-run mode and rate-limiting"""
    return request('GET', url, **kwargs)


@copy_signature(request, exclude='method')
def post(url: str, **kwargs) -> requests.Response:
    """Wrapper around :py:func:`requests.post` that supports dry-run mode and rate-limiting"""
    return request('POST', url, **kwargs)


@copy_signature(request, exclude='method')
def put(url: str, **kwargs) -> requests.Response:
    """Wrapper around :py:func:`requests.put` that supports dry-run mode and rate-limiting"""
    return request('PUT', url, **kwargs)


# TODO: This could be simplified after implementing:
#  https://github.com/vutran1710/PyrateLimiter/issues/19
@contextmanager
def apply_rate_limit():
    """Add delays in between requests to stay within the rate limits."""
    # Bypass rate-limiting for python 3.6
    n_retries = 0 if RATE_LIMITER else MAX_RETRIES

    while n_retries < MAX_RETRIES:
        # Check if there are more requests left in our "bucket"
        try:
            RATE_LIMITER.try_acquire(pyinaturalist.user_agent)
            break

        # If not, wait until there are
        except BucketFullException as e:
            if n_retries == 0:
                logger.info(e.message)
                logger.info('Rate limit reached; pausing before next request')
            # Abort if we've waited too long (e.g., we've likely reached the daily limit)
            elif n_retries == MAX_RETRIES:
                logger.error(f'Max retries ({MAX_RETRIES}) reached! Aborting request.')
                raise
            logger.info(f'Sleeping: {0.5 * (n_retries + 1)}')
            sleep(0.5 * (n_retries + 1))

        n_retries += 1

    yield


def get_session() -> requests.Session:
    """Get a Session object that will be reused across requests to take advantage of connection
    pooling. This is especially relevant for large paginated requests. If used in a multi-threaded
    context (for example, a :py:class:`~concurrent.futures.ThreadPoolExecutor`), a separate session
    is used for each thread.
    """
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session


def is_dry_run_enabled(method: str) -> bool:
    """A wrapper to determine if dry-run (aka test mode) has been enabled via either
    a constant or an environment variable. Dry-run mode may be enabled for either write
    requests, or all requests.
    """
    dry_run_enabled = pyinaturalist.DRY_RUN_ENABLED or env_to_bool('DRY_RUN_ENABLED')
    if method in WRITE_HTTP_METHODS:
        return (
            dry_run_enabled or pyinaturalist.DRY_RUN_WRITE_ONLY or env_to_bool('DRY_RUN_WRITE_ONLY')
        )
    return dry_run_enabled


def env_to_bool(environment_variable: str) -> bool:
    """Translate an environment variable to a boolean value, accounting for minor
    variations (case, None vs. False, etc.)
    """
    env_value = getenv(environment_variable)
    return bool(env_value) and str(env_value).lower() not in ['false', 'none']


def log_request(*args, **kwargs):
    """ Log all relevant information about an HTTP request """
    kwargs_strs = [f'{k}={v}' for k, v in kwargs.items()]
    logger.info('Request: {}'.format(', '.join(list(args) + kwargs_strs)))
