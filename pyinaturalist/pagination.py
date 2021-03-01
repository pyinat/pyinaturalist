from functools import wraps
from logging import getLogger
from math import ceil
from time import sleep
from typing import Callable

from pyinaturalist.constants import (
    EXPORT_URL,
    LARGE_REQUEST_WARNING,
    PER_PAGE_RESULTS,
    REQUESTS_PER_MINUTE,
    THROTTLING_DELAY,
    JsonResponse,
)

logger = getLogger(__name__)


def add_paginate_all(method: str = 'page'):
    """Decorator that adds auto-pagination support, invoked by passing ``page='all'`` to the wrapped
    API function.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(**params):
            if params.get('page') == 'all':
                return paginate_all(func, method=method, **params)
            return func(**params)

        return wrapper

    return decorator


def paginate_all(api_func: Callable, method: str = 'page', **params) -> JsonResponse:
    """Get all pages of a multi-page request. Explicit pagination parameters will be overridden.

    Args:
        api_func: API endpoint function to paginate
        method: Pagination method; either 'page' or 'id' (see below)
        params: Original request parameters

    Note on pagination by ID, from the iNaturalist documentation:
    _'The large size of the observations index prevents us from supporting the page parameter when
    retrieving records from large result sets. If you need to retrieve large numbers of records,
    use the ``per_page`` and ``id_above`` or ``id_below`` parameters instead.'_

    Returns:
        Response dict containing combined results, in the same format as ``api_func``
    """
    if method == 'id':
        params['order_by'] = 'id'
        params['order'] = 'asc'
    else:
        params['page'] = 1
    params['per_page'] = PER_PAGE_RESULTS

    # Run an initial request to get request size
    response = api_func(**params)
    results = page_results = response['results']
    total_results = response.get('total_results')
    estimate_request_size(total_results)

    # Some endpoints (like get_observation_fields) don't return total_results for some reason
    # Also check page size, in case total_results is off (race condition, outdated index, etc.)
    def check_results():
        more_results = total_results is None or len(results) < total_results
        return more_results and len(page_results) > 0

    # Loop until we get all pages
    while check_results():
        if method == 'id':
            params['id_above'] = page_results[-1]['id']
        else:
            params['page'] += 1

        page_results = api_func(**params).get('results', [])
        results += page_results
        sleep(THROTTLING_DELAY)

    return {
        'results': results,
        'total_results': len(results),
    }


def estimate_request_size(total_results):
    """Log the estimated total number of requests and rate-limiting delay, and show a warning if
    the request is too large
    """
    if not total_results:
        return
    total_requests = ceil(total_results / PER_PAGE_RESULTS)
    est_delay = ceil((total_requests / REQUESTS_PER_MINUTE) * 60)
    logger.info(
        f'This query will fetch {total_results} results in {total_requests} requests. '
        f'Estimated total rate-limiting delay: {est_delay} seconds'
    )

    if total_results > LARGE_REQUEST_WARNING:
        logger.warning(
            'This request is larger than recommended for API usage. For bulk requests, consider '
            f'using the iNat export tool instead: {EXPORT_URL}'
        )
