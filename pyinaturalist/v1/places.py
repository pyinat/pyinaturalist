from pyinaturalist import api_docs as docs
from pyinaturalist.constants import JsonResponse, MultiInt
from pyinaturalist.converters import convert_all_coordinates, convert_all_place_coordinates
from pyinaturalist.forge_utils import document_request_params
from pyinaturalist.pagination import add_paginate_all
from pyinaturalist.v1 import get_v1


def get_places_by_id(place_id: MultiInt, user_agent: str = None) -> JsonResponse:
    """
    Get one or more places by ID.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Places/get_places_id

    Example:
        >>> response = get_places_by_id([67591, 89191])
        >>> print(format_places(response))
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
    response = get_v1('places', ids=place_id, user_agent=user_agent)

    # Convert coordinates to floats
    places = response.json()
    places['results'] = convert_all_coordinates(places['results'])
    return places


@document_request_params([docs._bounding_box, docs._name])
def get_places_nearby(**params) -> JsonResponse:
    """
    Given an bounding box, and an optional name query, return places nearby

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Places/get_places_nearby

    Example:
        >>> bounding_box = (150.0, -50.0, -149.999, -49.999)
        >>> response = get_places_nearby(*bounding_box)

        Response is split into standard (curated) places and community (non-curated) places:

        >>> print(len(response['results']['standard']))
        10
        >>> print(len(response['results']['community']))
        10

        Show basic info for all places in response:

        >>> print(format_places(response))
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
    response = get_v1('places/nearby', params=params)
    return convert_all_place_coordinates(response.json())


@document_request_params([docs._search_query, docs._pagination])
@add_paginate_all(method='autocomplete')
def get_places_autocomplete(q: str = None, **params) -> JsonResponse:
    """Given a query string, get places with names starting with the search term

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Places/get_places_autocomplete

    **Note:** This endpoint accepts a ``per_page`` param, up to a max of 20 (default 10). Pages
    beyond the first page cannot be retrieved. Use ``page=all`` to attempt to retrieve additional
    results. See :py:func:`.paginate_autocomplete` for more info.

    Example:
        >>> response = get_places_autocomplete('Irkutsk')
        >>> print(format_places(response))
        [11803] Irkutsk
        [41854] Irkutskiy rayon
        [166186] Irkutsk Oblast - ADD
        [163077] Irkutsk agglomeration

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_places_autocomplete.py

    Args:
        q: Name must begin with this value

    Returns:
        Response dict containing place records
    """
    response = get_v1('places/autocomplete', params={'q': q, **params})

    # Convert coordinates to floats
    places = response.json()
    places['results'] = convert_all_coordinates(places['results'])
    return places
