from functools import wraps
from typing import Optional

from pyinaturalist.constants import API_V1, JsonResponse, MultiInt
from pyinaturalist.converters import convert_all_coordinates, convert_all_place_coordinates
from pyinaturalist.docs import document_request_params
from pyinaturalist.docs import templates as docs
from pyinaturalist.paginator import AutocompletePaginator, JsonPaginator
from pyinaturalist.session import get


def get_places_by_id(place_id: MultiInt, **params) -> JsonResponse:
    """Get one or more places by ID

    .. rubric:: Notes

    * API reference: :v1:`GET /places/{id} <Places/get_places_id>`

    Example:
        >>> response = get_places_by_id([67591, 89191])
        >>> pprint(response)
        [89191] Conservation Area Riversdale
        [67591] Riversdale Beach

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_places_by_id.py

    Args:
        place_id: Get a place with this ID. Multiple values are allowed.

    Returns:
        Response dict containing place records
    """
    response = get(f'{API_V1}/places', ids=place_id, **params)

    # Convert coordinates to floats
    places = response.json()
    places['results'] = convert_all_coordinates(places['results'])
    return places


@document_request_params(docs._bounding_box, docs._name)
def get_places_nearby(
    nelat: float, nelng: float, swlat: float, swlng: float, **params
) -> JsonResponse:
    """Search for places near a given location

    .. rubric:: Notes

    * API reference: :v1:`GET /places/nearby <get_places_nearby>`

    Example:
        >>> bounding_box = (150.0, -50.0, -149.999, -49.999)
        >>> response = get_places_nearby(*bounding_box)

        Response is split into standard (curated) places and community (non-curated) places:

        >>> print(len(response['results']['standard']))
        10
        >>> print(len(response['results']['community']))
        10

        Show basic info for all places in response:

        >>> pprint(response)
        [97394] North America
        [97395] Asia
        [97393] Oceania
        ...

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_places_nearby.py

    Returns:
        Response dict containing place records, divided into 'standard' and 'community' places.
    """
    response = get(
        f'{API_V1}/places/nearby', nelat=nelat, nelng=nelng, swlat=swlat, swlng=swlng, **params
    )
    return convert_all_place_coordinates(response.json())


@document_request_params(docs._search_query, docs._pagination)
def get_places_autocomplete(q: Optional[str] = None, **params) -> JsonResponse:
    """Given a query string, get places with names starting with the search term

    .. rubric:: Notes

    * API reference: :v1:`GET /places/autocomplete <Places/get_places_autocomplete>`
    * This endpoint accepts a ``per_page`` param, up to a max of 20 (default 10)
    * Pages beyond the first page cannot be retrieved. Use ``page=all`` to attempt to retrieve
      additional results. See :py:func:`.paginate_autocomplete` for more info.

    Example:
        >>> response = get_places_autocomplete('Irkutsk')
        >>> pprint(response)
        [11803] Irkutsk
        [41854] Irkutskiy rayon
        [166186] Irkutsk Oblast - ADD
        [163077] Irkutsk agglomeration

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_places_autocomplete.py

    Returns:
        Response dict containing place records
    """
    if params.get('page') == 'all':
        places = PlaceAutocompletePaginator(q=q, **params).all()
    else:
        places = get(f'{API_V1}/places/autocomplete', q=q, **params).json()

    places['results'] = convert_all_coordinates(places['results'])
    return places


class PlaceAutocompletePaginator(JsonPaginator, AutocompletePaginator):  # type: ignore
    def __init__(self, **kwargs):
        kwargs['per_page'] = 20

        @wraps(get)
        def reqeuest_function(**request_kwargs):
            return get(f'{API_V1}/places/autocomplete', **request_kwargs)

        super().__init__(reqeuest_function, **kwargs)
