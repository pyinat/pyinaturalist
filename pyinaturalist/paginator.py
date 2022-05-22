from collections import deque
from concurrent.futures import ThreadPoolExecutor
from logging import getLogger
from math import ceil
from typing import (
    AsyncIterable,
    AsyncIterator,
    Callable,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
)

from requests import Response

from pyinaturalist.constants import (
    EXPORT_URL,
    LARGE_REQUEST_WARNING,
    PER_PAGE_RESULTS,
    REQUESTS_PER_MINUTE,
    IntOrStr,
    JsonResponse,
    ResponseResult,
)
from pyinaturalist.models import T

logger = getLogger(__name__)


# TODO: Add per-endpoint 'max_per_page' parameter to use with Paginator.all()
class Paginator(Iterable, AsyncIterable, Generic[T]):
    """Class to handle pagination of API requests, with async support

    Args:
        request_function: API request function to paginate
        model: Model class to use for results
        method: Pagination method; either 'page' or 'id' (see note below)
        limit: Maximum number of total results to fetch
        per_page: Maximum number of results to fetch per page
        kwargs: Original request parameters


    .. note::
        Note on pagination by ID, from the iNaturalist documentation:

        *The large size of the observations index prevents us from supporting the page parameter
        when retrieving records from large result sets. If you need to retrieve large numbers of
        records, use the ``per_page`` and ``id_above`` or ``id_below`` parameters instead.*

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
        self.kwargs = kwargs
        self.request_function = request_function
        self.request_args = request_args
        self.method = method
        self.model = model
        self.total_limit = limit
        self.per_page = per_page or PER_PAGE_RESULTS

        self.exhausted = False
        self.results_fetched = 0
        self.total_results: Optional[int] = None

        # Set initial pagination params based on pagination method
        self.kwargs.pop('page', None)
        self.kwargs.pop('per_page', None)
        if self.method == 'id':
            self.kwargs['order_by'] = 'id'
            self.kwargs['order'] = 'asc'
        elif self.method == 'page':
            self.kwargs['page'] = 1

        if request_function:
            log_kwargs = {k: v for k, v in self.kwargs.items() if k != 'session'}
            logger.debug(
                f'Prepared paginated request: {self.request_function.__name__}'
                f'(args={self.request_args}, kwargs={log_kwargs})'
            )

    async def __aiter__(self) -> AsyncIterator[T]:
        """Iterate over paginated results, with non-blocking requests sent from a separate thread"""
        with ThreadPoolExecutor(max_workers=1) as executor:
            while not self.exhausted:
                for result in executor.submit(self.next_page).result():
                    yield result

    def __iter__(self) -> Iterator[T]:
        """Iterate over paginated results"""
        while not self.exhausted:
            for result in self.next_page():
                yield result

    def all(self) -> List[T]:
        """Get all results in a single list"""
        return list(self)

    def limit(self, limit: int) -> List[T]:
        """Get at most ``limit`` results"""
        self.total_limit = limit
        return list(self)

    def one(self) -> Optional[T]:
        """Get the first result from the query"""
        self.per_page = 1
        results = self.next_page()
        return results[0] if results else None

    def count(self) -> int:
        """Get the total number of results for this query, without fetching response data.

        Returns:
            Either the total number of results, if the endpoint provides pagination info, or ``-1``
        """
        if self.total_results is None:
            kwargs = {**self.kwargs, 'per_page': 0}
            count_response = self.request_function(*self.request_args, **kwargs)
            self.total_results = int(count_response['total_results'])
        return self.total_results

    def next_page(self) -> List[T]:
        """Get the next page of results, as model objects"""
        return self.model.from_json_list(self._next_page())

    def _next_page(self) -> List[ResponseResult]:
        """Get the next page of results, as raw JSON"""
        if self.exhausted:
            return []

        # If a limit is specified, avoid fetching more results than needed
        if self.total_limit and self.results_fetched + self.per_page > self.total_limit:
            self.per_page = self.total_limit - self.results_fetched

        # Fetch results; handle response object or dict
        response = self.request_function(*self.request_args, **self.kwargs, per_page=self.per_page)
        if isinstance(response, Response):
            response = response.json()
        results = response.get('results', response)

        # Note: For id-based pagination, only the first page's 'total_results' is accurate
        if self.total_results is None:
            self.total_results = response.get('total_results', len(results))

        # If this is the first of multiple requests, log the estimated time and number of requests
        self.results_fetched += len(results)
        self._update_next_page_params(results)
        if self.results_fetched == len(results) and not self.exhausted:
            self._estimate()

        return results

    def _check_exhausted(self, page_results: List = None):
        return (
            (self.total_limit and self.results_fetched >= self.total_limit)
            or (self.total_results and self.results_fetched >= self.total_results)
            or (self.per_page and page_results is not None and len(page_results) < self.per_page)
        )

    def _deduplicate(self, results) -> List[T]:
        """Deduplicate results by ID"""
        unique_results = {result.id: result for result in results}
        self.total_results = len(unique_results)
        return list(unique_results.values())

    def _update_next_page_params(self, page_results):
        """Set params for next request, if there are more results. Also check page size, in case
        total_results is off due to race condition, outdated index, etc.
        """
        if self._check_exhausted(page_results):
            self.exhausted = True
        elif self.method == 'id':
            self.kwargs['id_above'] = page_results[-1]['id']
        elif self.method == 'page':
            self.kwargs['page'] += 1

    def _estimate(self):
        """Log the estimated total number of requests and rate-limiting delay, and show a warning if
        the request is too large
        """
        total_requests = ceil(self.total_results / self.per_page)
        est_delay = ceil((total_requests / REQUESTS_PER_MINUTE) * 60) - 1
        logger.info(
            f'This query will fetch {self.total_results} results in {total_requests} requests. '
            f'Estimated total request time: {est_delay} seconds'
        )

        if self.total_results > LARGE_REQUEST_WARNING:
            logger.warning(
                'This request is larger than recommended for API usage. For bulk requests, consider '
                f'using the iNat export tool instead: {EXPORT_URL}'
            )

    def __str__(self) -> str:
        return (
            f'{self.__class__.__name__}(request_function={self.request_function.__name__}, '
            f'fetched={self.results_fetched}/{self.total_results or "unknown"})'
        )


class IDPaginator(Paginator):
    """Paginator for ID-based endpoints that only accept a limited number of IDs per request"""

    def __init__(self, *args, ids: Iterable[IntOrStr] = None, ids_per_request: int = 1, **kwargs):
        super().__init__(*args, **kwargs)
        if ids_per_request == 1:
            self.id_batches = deque(ids or [])
        else:
            self.id_batches = deque(list(chunkify(ids, ids_per_request)))  # type: ignore
        self.total_results = len(ids)  # type: ignore

    def _next_page(self) -> List[ResponseResult]:
        """Get the next record by ID"""
        try:
            next_ids = self.id_batches.popleft()
        except IndexError:
            self.exhausted = True
            return []

        response = self.request_function(next_ids, *self.request_args, **self.kwargs)
        self.results_fetched += 1
        return response['results'] if 'results' in response else [response]


class AutocompletePaginator(Paginator):
    """Paginator that attempts to get as many results as possible from an autocomplete endpoint.
    This is necessary for some problematic queries for which there are many matches but not ranked
    with the desired match(es) first.

    This works based on different rankings being returned for order_by=area. No other fields can be
    sorted on, and direction can't be specified, but this can at least provide a few additional
    results beyond the limit of 20.

    All results will be de-duplicated and returned as a single page. This may potentially be applied
    to other autocomplete endpoints, but so far is only needed for places.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kwargs.pop('page', None)
        self.kwargs.pop('order_by', None)

    def all(self) -> List[T]:
        """Get all results in a single de-duplicated list"""
        return self._deduplicate(list(self))

    def _update_next_page_params(self, page_results):
        """After the first request, update the order_by param. After the second request, we're done."""
        if (
            self._check_exhausted()
            or (self.per_page and self.results_fetched > self.per_page)
            or (self.per_page and len(page_results) < self.per_page)
            or len(page_results) == 0
        ):
            self.exhausted = True
        else:
            self.kwargs['order_by'] = 'area'


class JsonPaginator(Paginator):
    """Paginator that returns raw response dicts instead of model objects"""

    def __iter__(self) -> Iterator[ResponseResult]:
        """Iterate over paginated results, and skip conversion to model objects"""
        while not self.exhausted:
            for result in self._next_page():
                yield result

    def all(self) -> JsonResponse:  # type: ignore
        results = super().all()
        return {
            'results': results,
            'total_results': len(results),
        }

    def _deduplicate(self, results) -> List[T]:
        """Deduplicate results by ID"""
        unique_results = {result['id']: result for result in results}
        self.total_results = len(unique_results)
        return list(unique_results.values())


class WrapperPaginator(Paginator):
    """Paginator class that wraps results that have already been fetched."""

    def __init__(self, results: List[T], *args, **kwargs):
        super().__init__(None, None, *args, **kwargs)  # type: ignore  # no request_function
        self.results = results
        self.results_fetched = self.total_results = len(results)

    def count(self) -> int:
        return len(self.results)

    def next_page(self):
        self.exhausted = True
        return self.results


def chunkify(iterable: Iterable, max_size: int) -> Iterator[List]:
    """Split an iterable into chunks of a max size"""
    iterable = list(iterable)
    for index in range(0, len(iterable), max_size):
        yield iterable[index : index + max_size]


def paginate_all(request_function: Callable, *args, method: str = 'page', **kwargs) -> JsonResponse:
    """Get all pages of a multi-page request. Explicit pagination parameters will be overridden.

    Returns:
        Response dict containing combined results, in the same format as ``api_func``
    """
    return JsonPaginator(request_function, None, *args, method=method, **kwargs).all()
