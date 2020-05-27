# Some common functions for HTTP requests used by both the Node and REST API modules
from logging import getLogger
from os import getenv
from typing import Dict

import requests

import pyinaturalist
from pyinaturalist.constants import DRY_RUN_ENABLED, MOCK_RESPONSE
from pyinaturalist.helpers import preprocess_request_params

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

    if is_dry_run_enabled():
        log_request(method, url, params=params, headers=headers, **kwargs)
        return MOCK_RESPONSE
    else:
        return requests.request(method, url, params=params, headers=headers, **kwargs)


def is_dry_run_enabled() -> bool:
    """ A wrapper to determine if dry-run (aka test mode) has been enabled via either
    the constant or the environment variable
    """
    return DRY_RUN_ENABLED or getenv("DRY_RUN_ENABLED")


def log_request(*args, **kwargs):
    """ Log all relevant information about an HTTP request """
    kwargs_strs = ["{}={}".format(k, v) for k, v in kwargs.items()]
    logger.info('Request: {}'.format(', '.join(list(args) + kwargs_strs)))
