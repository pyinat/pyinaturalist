"""
Code to access the (read-only, but fast) Node based public iNaturalist API
See: http://api.inaturalist.org/v1/docs/
"""
from logging import getLogger
from time import sleep
from typing import Dict, Any, List

import requests
from urllib.parse import urljoin

from pyinaturalist.constants import (
    DEFAULT_OBSERVATION_ATTRS,
    INAT_NODE_API_BASE_URL,
    PER_PAGE_RESULTS,
    THROTTLING_DELAY,
)
from pyinaturalist.exceptions import ObservationNotFound
from pyinaturalist.request_params import is_int
from pyinaturalist.response_format import (
    format_taxon,
    as_geojson_feature_collection,
    _get_rank_range,
    flatten_nested_params,
)
from pyinaturalist.api_requests import get

logger = getLogger(__name__)


def make_inaturalist_api_get_call(
    endpoint: str, params: Dict, user_agent: str = None, **kwargs
) -> requests.Response:
    """Make an API call to iNaturalist.

    Args:
        endpoint: The name of an endpoint not including the base URL e.g. 'observations'
        kwargs: Arguments for :py:func:`requests.request`
    """
    response = get(
        urljoin(INAT_NODE_API_BASE_URL, endpoint), params=params, user_agent=user_agent, **kwargs
    )
    return response


def get_observation(observation_id: int, user_agent: str = None) -> Dict[str, Any]:
    """Get details about an observation.

    Args:
        observation_id: Observation ID
        user_agent: a user-agent string that will be passed to iNaturalist.

    Returns:
        A dict with details on the observation

    Raises:
        ObservationNotFound
    """

    r = get_observations(params={"id": observation_id}, user_agent=user_agent)
    if r["results"]:
        return r["results"][0]

    raise ObservationNotFound()


def get_observations(params: Dict, user_agent: str = None) -> Dict[str, Any]:
    """Search observations.
    See: http://api.inaturalist.org/v1/docs/#!/Observations/get_observations.

    Returns:
        The parsed JSON returned by iNaturalist (observations in r['results'], a list of dicts)
    """

    r = make_inaturalist_api_get_call("observations", params=params, user_agent=user_agent)
    return r.json()


def get_all_observations(params: Dict, user_agent: str = None) -> List[Dict[str, Any]]:
    """Like get_observations() but handles pagination so you get all the results in one shot.

    Some params will be overwritten: order_by, order, per_page, id_above (do NOT specify page when using this).

    Returns:
        A list of dicts (one entry per observation)
    """

    # According to the doc: "The large size of the observations index prevents us from supporting the page parameter
    # when retrieving records from large result sets. If you need to retrieve large numbers of records, use the
    # per_page and id_above or id_below parameters instead.

    results = []  # type: List[Dict[str, Any]]
    id_above = 0
    pagination_params = {
        **params,
        **{"order_by": "id", "order": "asc", "per_page": PER_PAGE_RESULTS},
    }

    while True:
        pagination_params["id_above"] = id_above

        page_obs = get_observations(params=pagination_params, user_agent=user_agent)
        results = results + page_obs.get("results", [])

        if page_obs["total_results"] <= PER_PAGE_RESULTS:
            return results

        sleep(THROTTLING_DELAY)
        id_above = results[-1]["id"]


def get_geojson_observations(properties: List[str] = None, **kwargs) -> Dict[str, Any]:
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

    Args:
        properties: Properties from observation results to include as GeoJSON properties
        kwargs: Arguments for :py:func:`.get_observations`

    Returns:
        A ``FeatureCollection`` containing observation results as ``Feature`` dicts.
    """
    kwargs["mappable"] = True
    observations = get_all_observations(kwargs)
    return as_geojson_feature_collection(
        (flatten_nested_params(obs) for obs in observations),
        properties=properties if properties is not None else DEFAULT_OBSERVATION_ATTRS,
    )


def get_taxa_by_id(taxon_id: int, user_agent: str = None) -> Dict[str, Any]:
    """
    Get one or more taxa by ID.
    See: https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa_id

    Args:
        taxon_id: Get taxa with this ID. Multiple values are allowed.

    Returns:
        A list of dicts containing taxa results
    """
    if not is_int(taxon_id):
        raise ValueError("Please specify a single integer for the taxon ID")
    r = make_inaturalist_api_get_call("taxa/{}".format(taxon_id), {}, user_agent=user_agent)
    r.raise_for_status()
    return r.json()


def get_taxa(
    user_agent: str = None, min_rank: str = None, max_rank: str = None, **params
) -> Dict[str, Any]:
    """Given zero to many of following parameters, returns taxa matching the search criteria.
    See https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa

    Args:
        q: Name must begin with this value
        is_active: Taxon is active
        taxon_id: Only show taxa with this ID, or its descendants
        parent_id: Taxon's parent must have this ID
        rank: Taxon must have this exact rank
        min_rank: Taxon must have this rank or higher; overrides ``rank``
        max_rank: Taxon must have this rank or lower; overrides ``rank``
        rank_level: Taxon must have this rank level. Some example values are 70 (kingdom), 60 (phylum),
            50 (class), 40 (order), 30 (family), 20 (genus), 10 (species), 5 (subspecies)
        id_above: Must have an ID above this value
        id_below: Must have an ID below this value
        per_page: Number of results to return in a page. The maximum value is generally 200 unless
            otherwise noted
        locale: Locale preference for taxon common names
        preferred_place_id: Place preference for regional taxon common names
        only_id: Return only the record IDs
        all_names: Include all taxon names in the response

    Returns:
        A list of dicts containing taxa results
    """
    if min_rank or max_rank:
        params["rank"] = _get_rank_range(min_rank, max_rank)
    r = make_inaturalist_api_get_call("taxa", params, user_agent=user_agent)
    r.raise_for_status()
    return r.json()


def get_taxa_autocomplete(user_agent: str = None, minify: bool = False, **params) -> Dict[str, Any]:
    """Given a query string, returns taxa with names starting with the search term
    See: https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa_autocomplete

    **Note:** There appears to currently be a bug in the API that causes ``per_page`` to not have
    any effect.

    Args:
        q: Name must begin with this value
        is_active: Taxon is active
        taxon_id: Only show taxa with this ID, or its descendants
        rank: Taxon must have this rank
        rank_level: Taxon must have this rank level. Some example values are 70 (kingdom),
            60 (phylum), 50 (class), 40 (order), 30 (family), 20 (genus), 10 (species), 5 (subspecies)
        per_page: Number of results to return in a page. The maximum value is generally 200 unless otherwise noted
        locale: Locale preference for taxon common names
        preferred_place_id: Place preference for regional taxon common names
        all_names: Include all taxon names in the response
        minify: Condense each match into a single string containg taxon ID, rank, and name

    Returns:
        A list of dicts containing taxa results
    """
    r = make_inaturalist_api_get_call("taxa/autocomplete", params, user_agent=user_agent)
    r.raise_for_status()
    json_response = r.json()

    if minify:
        json_response["results"] = [format_taxon(t) for t in json_response["results"]]
    return json_response
