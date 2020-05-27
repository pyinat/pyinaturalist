# Some common functions for HTTP requests used by both the Node and REST API modules
import requests
from typing import Dict

import pyinaturalist
from pyinaturalist.constants import DRY_RUN_ENABLED, MOCK_RESPONSE
from pyinaturalist.helpers import preprocess_request_params


def delete(url: str, **kwargs) -> requests.Response:
    """Wrapper around :py:func:`requests.delete` that supports dry-run mode"""
    return request("DELETE", url, **kwargs)


def get(url: str, **kwargs) -> requests.Response:
    """Wrapper around :py:func:`requests.get` that supports dry-run mode"""
    return request("GET", url, **kwargs)


def post(url: str, **kwargs) -> requests.Response:
    """Wrapper around :py:func:`requests.post` that supports dry-run mode"""
    return request("POST", url, **kwargs)


def put(url: str, **kwargs) -> requests.Response:
    """Wrapper around :py:func:`requests.put` that supports dry-run mode"""
    return request("PUT", url, **kwargs)


def request(
    method: str,
    url: str,
    access_token: str = None,
    user_agent: str = None,
    params: Dict = None,
    headers: Dict = None,
    **kwargs
) -> requests.Response:
    """Wrapper around :py:func:`requests.request` that supports dry-run mode and
    adds appropriate headers.

    :param method: HTTP method
    :param url: Request URL
    :param access_token: access_token: the access token, as returned by :func:`get_access_token()`
    :param user_agent: a user-agent string that will be passed to iNaturalist

    """
    # Set user agent and authentication headers, if specified
    headers = headers or {}
    headers["Accept"] = "application/json"
    headers["User-Agent"] = user_agent or pyinaturalist.user_agent
    if access_token:
        headers["Authorization"] = "Bearer %s" % access_token
    params = preprocess_request_params(params)

    return requests.request(method, url, params=params, headers=headers, **kwargs)


# Make dryable an optional dependency; if it is not installed, its decorator will not be applied.
# Dryable must be both installed and enabled before requests are mocked.
try:
    import dryable

    dryable.set(DRY_RUN_ENABLED)
    request = dryable.Dryable(value=MOCK_RESPONSE)(request)
except ImportError:
    pass
