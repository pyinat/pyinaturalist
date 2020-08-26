"""
Code to access the (read-only, but fast) Node based public iNaturalist API
See: http://api.inaturalist.org/v1/docs/
"""
from logging import getLogger
from time import sleep
from typing import Dict, List
from warnings import warn

import requests
from urllib.parse import urljoin

from pyinaturalist.api_docs import (
    document_request_params,
    get_observations_params,
    get_all_observations_params,
    get_observation_species_counts_params,
    get_geojson_observations_params,
    get_places_nearby_params,
    get_taxa_params,
    get_taxa_autocomplete_params,
)
from pyinaturalist.constants import (
    DEFAULT_OBSERVATION_ATTRS,
    INAT_NODE_API_BASE_URL,
    PER_PAGE_RESULTS,
    THROTTLING_DELAY,
    MultiInt,
    JsonResponse,
)
from pyinaturalist.exceptions import ObservationNotFound
from pyinaturalist.request_params import (
    check_deprecated_params,
    is_int,
    is_int_list,
    translate_rank_range,
)
from pyinaturalist.response_format import (
    format_taxon,
    as_geojson_feature_collection,
    flatten_nested_params,
    convert_location_to_float,
)
from pyinaturalist.api_requests import get

logger = getLogger(__name__)


def make_inaturalist_api_get_call(endpoint: str, **kwargs) -> requests.Response:
    """Make an API call to iNaturalist.

    Args:
        endpoint: The name of an endpoint not including the base URL e.g. 'observations'
        kwargs: Arguments for :py:func:`.api_requests.request`
    """
    return get(urljoin(INAT_NODE_API_BASE_URL, endpoint), **kwargs)


def get_observation(observation_id: int, user_agent: str = None) -> JsonResponse:
    """Get details about an observation.

    Args:
        observation_id: Observation ID
        user_agent: a user-agent string that will be passed to iNaturalist.

    Returns:
        A dict with details on the observation

    Raises:
        ObservationNotFound
    """

    r = get_observations(id=observation_id, user_agent=user_agent)
    if r["results"]:
        return r["results"][0]

    raise ObservationNotFound()


@document_request_params(get_observations_params)
def get_observations(params: Dict = None, user_agent: str = None, **kwargs) -> JsonResponse:
    """ Search observations.
    See: http://api.inaturalist.org/v1/docs/#!/Observations/get_observations

    Returns:
        JSON response containing observation records
    """
    kwargs = check_deprecated_params(params, **kwargs)
    r = make_inaturalist_api_get_call("observations", params=kwargs, user_agent=user_agent)
    return r.json()


@document_request_params(get_all_observations_params)
def get_all_observations(
    params: Dict = None, user_agent: str = None, **kwargs
) -> List[JsonResponse]:
    """ Like :py:func:`get_observations()`, but handles pagination and returns all results in one
    call. Explicit pagination parameters will be ignored.

    Notes on pagination from the iNaturalist documentation:
    "The large size of the observations index prevents us from supporting the page parameter when
    retrieving records from large result sets. If you need to retrieve large numbers of records,
    use the ``per_page`` and ``id_above`` or ``id_below`` parameters instead."

    Returns:
        Combined list of observation records
    """
    kwargs = check_deprecated_params(params, **kwargs)
    if "page" in kwargs:
        warn("Cannot specify `page` parameter for this function; see API documentation")
        del kwargs["page"]

    results = []  # type: List[JsonResponse]
    id_above = 0
    pagination_params = {
        **kwargs,
        **{
            "order_by": "id",
            "order": "asc",
            "per_page": PER_PAGE_RESULTS,
            "user_agent": user_agent,
        },
    }

    while True:
        pagination_params["id_above"] = id_above
        page_obs = get_observations(**pagination_params)
        results = results + page_obs.get("results", [])

        if page_obs["total_results"] <= PER_PAGE_RESULTS:
            return results

        sleep(THROTTLING_DELAY)
        id_above = results[-1]["id"]


@document_request_params(get_observation_species_counts_params)
def get_observation_species_counts(user_agent: str = None, **kwargs) -> JsonResponse:
    """ Get all species (or other "leaf taxa") associated with observations matching the search
    criteria, and the count of observations they are associated with.
    **Leaf taxa** are the leaves of the taxonomic tree, e.g., species, subspecies, variety, etc.

    See: https://api.inaturalist.org/v1/docs/#!/Observations/get_observations_species_counts

    Example:
        >>> get_observation_species_counts(user_login='my_username', quality_grade='research')
        {
            'total_results': 214,
            'page': 1,
            'per_page': 500,
            'results': [
                {'count': 12, 'taxon': {'...'}},
            ]
        }

    """
    r = make_inaturalist_api_get_call(
        "observations/species_counts", params=kwargs, user_agent=user_agent,
    )
    r.raise_for_status()
    return r.json()


@document_request_params(get_geojson_observations_params)
def get_geojson_observations(properties: List[str] = None, **kwargs) -> JsonResponse:
    """ Get all observation results combined into a GeoJSON ``FeatureCollection``.
    By default this includes some basic observation properties as GeoJSON ``Feature`` properties.
    The ``properties`` argument can be used to override these defaults.

    Example:
        >>> get_geojson_observations(observation_id=16227955, properties=["photo_url"])
        {"type": "FeatureCollection",
            "features": [{
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [4.360086, 50.646894]},
                    "properties": {
                        "photo_url": "https://static.inaturalist.org/photos/24355315/square.jpeg?1536150659"
                    }
                }
            ]
        }

    Returns:
        A ``FeatureCollection`` containing observation results as ``Feature`` dicts.
    """
    kwargs["mappable"] = True
    observations = get_all_observations(**kwargs)
    return as_geojson_feature_collection(
        (flatten_nested_params(obs) for obs in observations),
        properties=properties if properties is not None else DEFAULT_OBSERVATION_ATTRS,
    )


def get_places_by_id(place_id: MultiInt, user_agent: str = None) -> JsonResponse:
    """
    Get one or more places by ID.
    See: https://api.inaturalist.org/v1/docs/#!/Places/get_places_id

    Example:
        >>> get_places_by_id(93735)
        {
            "total_results": 1,
            "page": 1,
            "per_page": 2,
            "results": ['...']
        }

    Args:
        place_id: Get a place with this ID. Multiple values are allowed.

    Returns:
        A list of dicts containing places results
    """
    if not (is_int(place_id) or is_int_list(place_id)):
        raise ValueError("Invalid ID(s); must specify integers only")
    r = make_inaturalist_api_get_call("places", resources=place_id, user_agent=user_agent)
    r.raise_for_status()

    # Convert coordinates to floats
    response = r.json()
    response["results"] = convert_location_to_float(response["results"])
    return response


@document_request_params(get_places_nearby_params)
def get_places_nearby(user_agent: str = None, **kwargs) -> JsonResponse:
    """
    Given an bounding box, and an optional name query, return standard iNaturalist curator approved
    and community non-curated places nearby
    See: https://api.inaturalist.org/v1/docs/#!/Places/get_places_nearby

    Example:
        >>> bounding_box = (150.0, -50.0, -149.999, -49.999)
        >>> get_places_nearby(*bounding_box)
        {
            "total_results": 20,
            "page": 1,
            "per_page": 20,
            "results": {
                "standard": ['...'],
                "community": ['...']
            }
        }

    Returns:
        A list of dicts containing places results
    """
    r = make_inaturalist_api_get_call("places/nearby", params=kwargs, user_agent=user_agent)
    r.raise_for_status()
    return _convert_all_locations_to_float(r.json())


def _convert_all_locations_to_float(response):
    """ Convert locations for both standard (curated) and community-contributed places to floats """
    response["results"] = {
        "standard": convert_location_to_float(response["results"].get("standard")),
        "community": convert_location_to_float(response["results"].get("community")),
    }
    return response


def get_places_autocomplete(q: str, user_agent: str = None) -> JsonResponse:
    """ Given a query string, get places with names starting with the search term
    See: https://api.inaturalist.org/v1/docs/#!/Places/get_places_autocomplete

    Example:
        >>> get_places_autocomplete('Irkutsk')
        {
            'total_results': 8,
            'page': 1,
            'per_page': 8,
            'results': ['...']
        }

    Args:
        q: Name must begin with this value

    Returns:
        A list of dicts containing places results
    """
    r = make_inaturalist_api_get_call("places/autocomplete", params={"q": q}, user_agent=user_agent)
    r.raise_for_status()

    # Convert coordinates to floats
    response = r.json()
    response["results"] = convert_location_to_float(response["results"])
    return response


def get_taxa_by_id(taxon_id: MultiInt, user_agent: str = None) -> JsonResponse:
    """ Get one or more taxa by ID.
    See: https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa_id

    Args:
        taxon_id: Get taxa with this ID. Multiple values are allowed.

    Returns:
        A list of dicts containing taxa results
    """
    if not (is_int(taxon_id) or is_int_list(taxon_id)):
        raise ValueError("Invalid ID(s); must specify integers only")
    r = make_inaturalist_api_get_call("taxa", resources=taxon_id, user_agent=user_agent)
    r.raise_for_status()
    return r.json()


@document_request_params(get_taxa_params)
def get_taxa(user_agent: str = None, **kwargs) -> JsonResponse:
    """Given zero to many of following parameters, returns taxa matching the search criteria.
    See https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa

    Returns:
        A list of dicts containing taxa results
    """
    kwargs = translate_rank_range(kwargs)
    r = make_inaturalist_api_get_call("taxa", params=kwargs, user_agent=user_agent)
    r.raise_for_status()
    return r.json()


@document_request_params(get_taxa_autocomplete_params)
def get_taxa_autocomplete(user_agent: str = None, **kwargs) -> JsonResponse:
    """Given a query string, returns taxa with names starting with the search term
    See: https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa_autocomplete

    **Note:** There appears to currently be a bug in the API that causes ``per_page`` to not have
    any effect.

    Returns:
        A list of dicts containing taxa results
    """
    kwargs = translate_rank_range(kwargs)
    r = make_inaturalist_api_get_call("taxa/autocomplete", params=kwargs, user_agent=user_agent)
    r.raise_for_status()
    json_response = r.json()

    if kwargs.get("minify"):
        json_response["results"] = [format_taxon(t) for t in json_response["results"]]
    return json_response
