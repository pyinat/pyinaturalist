from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from logging import getLogger
from math import ceil
from typing import AsyncIterable, AsyncIterator, Callable, Generic, Iterable, Iterator, List

from requests import Response

from pyinaturalist.constants import (
    EXPORT_URL,
    LARGE_REQUEST_WARNING,
    PER_PAGE_RESULTS,
    REQUESTS_PER_MINUTE,
    JsonResponse,
    ResponseResult,
)
from pyinaturalist.models import T

logger = getLogger(__name__)


# TODO: support autocomplete pseudo-pagination?
class Paginator(Iterable, AsyncIterable, Generic[T]):
    """Class to handle pagination of API requests, with async support

    Args:
        request_function: API request function to paginate
        model: Model class to use for results
        method: Pagination method; either 'page', 'id', or 'autocomplete' (see below)
        limit: Maximum number of results to fetch
        per_page: Maximum number of results to fetch per page
        kwargs: Original request parameters


    Note on pagination by ID, from the iNaturalist documentation:
    _'The large size of the observations index prevents us from supporting the page parameter when
    retrieving records from large result sets. If you need to retrieve large numbers of records,
    use the ``per_page`` and ``id_above`` or ``id_below`` parameters instead.'_

    """

    def __init__(
        self,
        request_function: Callable,
        model: T,
        *request_args,
        method: str = 'page',
        limit: int = None,
        per_page: int = None,
        **kwargs,
    ):
        self.limit = limit
        self.kwargs = kwargs
        self.request_function = request_function
        self.request_args = request_args
        self.method = method
        self.model = model
        self.per_page = per_page or PER_PAGE_RESULTS

        self.exhausted = False
        self.results_fetched = 0
        self._total_results = -1

        # Set initial pagination params based on pagination method
        self.kwargs.pop('page', None)
        self.kwargs.pop('per_page', None)
        # if self.method == 'autocomplete':
        #     return paginate_autocomplete(self.request_function, **self.kwargs)
        if self.method == 'id':
            self.kwargs['order_by'] = 'id'
            self.kwargs['order'] = 'asc'
        else:
            self.kwargs['page'] = 1

    async def __aiter__(self) -> AsyncIterator[T]:
        """Iterate over paginated results, with non-blocking requests sent from a separate thread"""
        with ThreadPoolExecutor(max_workers=1) as executor:
            while not self.exhausted:
                for result in executor.submit(self.next_page).result():
                    yield self.model.from_json(result)

    def __iter__(self) -> Iterator[T]:
        """Iterate over paginated results"""
        while not self.exhausted:
            for result in self.next_page():
                yield self.model.from_json(result)

    @property
    def total_results(self) -> int:
        """Total number of results for this query. Will be fetched if no pages have been fetched
        yet.
        """
        if self._total_results == -1:
            count_response = self.request_function(
                *self.request_args, **{**self.kwargs, 'per_page': 0}
            )
            self._total_results = int(count_response['total_results'])
        return self._total_results

    def all(self) -> List[T]:
        """Get all results in a single list"""
        return list(self)

    def next_page(self) -> List[ResponseResult]:
        """Get the next page of results"""
        if self.exhausted:
            return []

        # If a limit is specified, avoid fetching more results than needed
        if self.limit and self.results_fetched + self.per_page > self.limit:
            self.per_page = self.limit - self.results_fetched

        # Fetch results
        response = self.request_function(*self.request_args, **self.kwargs, per_page=self.per_page)
        if isinstance(response, Response):
            response = response.json()
        results = response.get('results', response)
        self._total_results = response.get('total_results', 0)
        self.results_fetched += len(results)

        # Set params for next request, if there are more results
        # Some endpoints (like get_observation_fields) don't return total_results
        # Also check page size, in case total_results is off (race condition, outdated index, etc.)
        if (
            (self.limit and self.results_fetched >= self.limit)
            or (self.total_results and self.results_fetched >= self.total_results)
            or len(results) == 0
        ):
            self.exhausted = True
        else:
            if self.method == 'id':
                self.kwargs['id_above'] = results[-1]['id']
            else:
                self.kwargs['page'] += 1

        # If this is the first of multiple requests, log the estimated time and number of requests
        if self.results_fetched == len(results) and not self.exhausted:
            self._estimate()
        return results

    def _estimate(self):
        """Log the estimated total number of requests and rate-limiting delay, and show a warning if
        the request is too large
        """
        total_requests = ceil(self.total_results / self.per_page)
        est_delay = ceil((total_requests / REQUESTS_PER_MINUTE) * 60)
        logger.info(
            f'This query will fetch {self.total_results} results in {total_requests} requests. '
            f'Estimated total rate-limiting delay: {est_delay} seconds'
        )

        if self.total_results > LARGE_REQUEST_WARNING:
            logger.warning(
                'This request is larger than recommended for API usage. For bulk requests, consider '
                f'using the iNat export tool instead: {EXPORT_URL}'
            )

    def __str__(self) -> str:
        return (
            f'Paginator({self.request_function.__name__}, '
            f'fetched={self.results_fetched}/{self.total_results})'
        )


class JsonPaginator(Paginator):
    """Paginator that returns raw response dicts instead of model objects"""

    def __iter__(self) -> Iterator[ResponseResult]:
        """Iterate over paginated results"""
        while not self.exhausted:
            for result in self.next_page():
                yield result

    def all(self) -> JsonResponse:  # type: ignore
        results = list(self)
        return {
            'results': results,
            'total_results': len(results),
        }


def add_paginate_all(method: str = 'page'):
    """Decorator that adds an option ``page='all'`` to get all pages of results for the wrapped API
    request function.
    """

    def decorator(request_function: Callable):
        @wraps(request_function)
        def wrapper(*args, **kwargs):
            if kwargs.get('page') == 'all':
                return paginate_all(request_function, *args, method=method, **kwargs)
            return request_function(*args, **kwargs)

        return wrapper

    return decorator


def paginate_all(request_function: Callable, *args, method: str = 'page', **kwargs) -> JsonResponse:
    """Get all pages of a multi-page request. Explicit pagination parameters will be overridden.

    Returns:
        Response dict containing combined results, in the same format as ``api_func``
    """
    if method == 'autocomplete':
        return paginate_autocomplete(request_function, *args, **kwargs)
    return JsonPaginator(request_function, None, *args, method=method, **kwargs).all()


def paginate_autocomplete(api_func: Callable, *args, **kwargs) -> JsonResponse:
    """Attempt to get as many results as possible from the places autocomplete endpoint.
    This is necessary for some problematic places for which there are many matches but not ranked
    with the desired match(es) first.

    This works based on different rankings being returned for order_by=area. No other fields can be
    sorted on, and direction can't be specified, but this can at least provide a few additional
    results beyond the limit of 20.
    """
    kwargs['per_page'] = 20
    kwargs.pop('order_by', None)

    # Search with default ordering and ordering by area (if there are more than 20 results)
    page_1 = api_func(*args, **kwargs)
    if page_1['total_results'] > 20:
        page_2 = api_func(*args, **kwargs, order_by='area')
    else:
        page_2 = {'results': []}

    # De-duplicate results
    unique_results = {r['id']: r for page in [page_1, page_2] for r in page['results']}
    return {
        'results': list(unique_results.values()),
        'total_results': page_1['total_results'],
    }
