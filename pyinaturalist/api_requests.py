""" Some common functions for HTTP requests used by both the Node and REST API modules """
from logging import getLogger
from os import getenv
from typing import Dict
from unittest.mock import Mock

import requests

import pyinaturalist
from pyinaturalist.constants import WRITE_HTTP_METHODS
from pyinaturalist.request_params import preprocess_request_params

# Mock response content to return in dry-run mode
MOCK_RESPONSE = Mock(spec=requests.Response)
MOCK_RESPONSE.json.return_value = {"results": ["nodata"]}

logger = getLogger(__name__)


def delete(url: str, **kwargs) -> requests.Response:
    """ Wrapper around :py:func:`requests.delete` that supports dry-run mode """
    return request("DELETE", url, **kwargs)


def get(url: str, **kwargs) -> requests.Response:
    """ Wrapper around :py:func:`requests.get` that supports dry-run mode """
    return request("GET", url, **kwargs)


def post(url: str, **kwargs) -> requests.Response:
    """ Wrapper around :py:func:`requests.post` that supports dry-run mode """
    return request("POST", url, **kwargs)


def put(url: str, **kwargs) -> requests.Response:
    """ Wrapper around :py:func:`requests.put` that supports dry-run mode """
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
    """ Wrapper around :py:func:`requests.request` that supports dry-run mode and
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

    if is_dry_run_enabled(method):
        logger.debug("Dry-run mode enabled; mocking request")
        log_request(method, url, params=params, headers=headers, **kwargs)
        return MOCK_RESPONSE
    else:
        return requests.request(method, url, params=params, headers=headers, **kwargs)


def is_dry_run_enabled(method: str) -> bool:
    """ A wrapper to determine if dry-run (aka test mode) has been enabled via either
    a constant or an environment variable. Dry-run mode may be enabled for either write
    requests, or all requests.
    """
    dry_run_enabled = pyinaturalist.DRY_RUN_ENABLED or env_to_bool("DRY_RUN_ENABLED")
    if method in WRITE_HTTP_METHODS:
        return (
            dry_run_enabled or pyinaturalist.DRY_RUN_WRITE_ONLY or env_to_bool("DRY_RUN_WRITE_ONLY")
        )
    return dry_run_enabled


def env_to_bool(environment_variable: str) -> bool:
    """ Translate an environment variable to a boolean value, accounting for minor
    variations (case, None vs. False, etc.)
    """
    env_value = getenv(environment_variable)
    return bool(env_value) and str(env_value).lower() not in ["false", "none"]


def log_request(*args, **kwargs):
    """ Log all relevant information about an HTTP request """
    kwargs_strs = ["{}={}".format(k, v) for k, v in kwargs.items()]
    logger.info("Request: {}".format(", ".join(list(args) + kwargs_strs)))
