"""
Code to access the (read-only, but fast) Node based public iNaturalist API
See: http://api.inaturalist.org/v1/docs/
"""
from logging import getLogger
from time import sleep
from typing import Dict, List

import requests
from urllib.parse import urljoin

from pyinaturalist import docstrings
from pyinaturalist.constants import (
    DEFAULT_OBSERVATION_ATTRS,
    INAT_NODE_API_BASE_URL,
    PER_PAGE_RESULTS,
    THROTTLING_DELAY,
    MultiInt,
    MultiStr,
    Date,
    DateTime,
    IntOrStr,
    JsonResponse,
)
from pyinaturalist.exceptions import ObservationNotFound
from pyinaturalist.request_params import is_int, is_int_list
from pyinaturalist.response_format import (
    format_taxon,
    as_geojson_feature_collection,
    _get_rank_range,
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

    r = get_observations(params={"id": observation_id}, user_agent=user_agent)
    if r["results"]:
        return r["results"][0]

    raise ObservationNotFound()


def get_observations(params: Dict, user_agent: str = None) -> JsonResponse:
    """Search observations.
    See: http://api.inaturalist.org/v1/docs/#!/Observations/get_observations

    Returns:
        The parsed JSON returned by iNaturalist (observations in r['results'], a list of dicts)
    """

    r = make_inaturalist_api_get_call("observations", params=params, user_agent=user_agent)
    return r.json()


def get_all_observations(params: Dict, user_agent: str = None) -> List[JsonResponse]:
    """Like get_observations() but handles pagination so you get all the results in one shot.

    Some params will be overwritten: order_by, order, per_page, id_above (do NOT specify page when using this).

    Returns:
        A list of dicts (one entry per observation)
    """

    # According to the doc: "The large size of the observations index prevents us from supporting the page parameter
    # when retrieving records from large result sets. If you need to retrieve large numbers of records, use the
    # per_page and id_above or id_below parameters instead.
    results = []  # type: List[JsonResponse]
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


# TODO: These explicit kwargs are useful but super verbose...
# TODO: It may be helpful to programmatically modify the function signature for a bit of code reuse
def get_observation_species_counts(
    acc: bool = None,
    captive: bool = None,
    endemic: bool = None,
    geo: bool = None,
    id_please: bool = None,
    identified: bool = None,
    introduced: bool = None,
    mappable: bool = None,
    native: bool = None,
    out_of_range: bool = None,
    pcid: bool = None,
    photos: bool = None,
    popular: bool = None,
    sounds: bool = None,
    taxon_is_active: bool = None,
    threatened: bool = None,
    verifiable: bool = None,
    id: MultiInt = None,
    not_id: MultiInt = None,
    license: MultiStr = None,
    photo_license: MultiStr = None,
    sound_license: MultiStr = None,
    ofv_datatype: MultiStr = None,
    place_id: MultiInt = None,
    project_id: MultiInt = None,
    rank: MultiStr = None,
    site_id: MultiStr = None,
    taxon_id: MultiInt = None,
    without_taxon_id: MultiInt = None,
    taxon_name: MultiStr = None,
    user_id: MultiInt = None,
    user_login: MultiStr = None,
    day: MultiInt = None,
    month: MultiInt = None,
    year: MultiInt = None,
    term_id: MultiInt = None,
    term_value_id: MultiInt = None,
    without_term_value_id: MultiInt = None,
    acc_above: str = None,
    acc_below: str = None,
    d1: Date = None,
    d2: Date = None,
    created_d1: DateTime = None,
    created_d2: DateTime = None,
    created_on: Date = None,
    observed_on: Date = None,
    unobserved_by_user_id: int = None,
    apply_project_rules_for: str = None,
    cs: str = None,
    csa: str = None,
    csi: MultiStr = None,
    geoprivacy: MultiStr = None,
    taxon_geoprivacy: MultiStr = None,
    max_rank: str = None,
    min_rank: str = None,
    hrank: str = None,
    lrank: str = None,
    iconic_taxa: MultiStr = None,
    id_above: int = None,
    id_below: int = None,
    identifications: str = None,
    lat: float = None,
    lng: float = None,
    radius: float = None,
    nelat: float = None,
    nelng: float = None,
    swlat: float = None,
    swlng: float = None,
    list_id: int = None,
    not_in_project: IntOrStr = None,
    not_matching_project_rules_for: IntOrStr = None,
    q: str = None,
    search_on: str = None,
    quality_grade: str = None,
    updated_since: DateTime = None,
    viewer_id: int = None,
    reviewed: bool = None,
    locale: str = None,
    preferred_place_id: int = None,
    ttl: str = None,
    user_agent: str = None,
) -> JsonResponse:
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
    params = {
        "acc": acc,
        "captive": captive,
        "endemic": endemic,
        "geo": geo,
        "id_please": id_please,
        "identified": identified,
        "introduced": introduced,
        "mappable": mappable,
        "native": native,
        "out_of_range": out_of_range,
        "pcid": pcid,
        "photos": photos,
        "popular": popular,
        "sounds": sounds,
        "taxon_is_active": taxon_is_active,
        "threatened": threatened,
        "verifiable": verifiable,
        "id": id,
        "not_id": not_id,
        "license": license,
        "photo_license": photo_license,
        "sound_license": sound_license,
        "ofv_datatype": ofv_datatype,
        "place_id": place_id,
        "project_id": project_id,
        "rank": rank,
        "site_id": site_id,
        "taxon_id": taxon_id,
        "without_taxon_id": without_taxon_id,
        "taxon_name": taxon_name,
        "user_id": user_id,
        "user_login": user_login,
        "day": day,
        "month": month,
        "year": year,
        "term_id": term_id,
        "term_value_id": term_value_id,
        "without_term_value_id": without_term_value_id,
        "acc_above": acc_above,
        "acc_below": acc_below,
        "d1": d1,
        "d2": d2,
        "created_d1": created_d1,
        "created_d2": created_d2,
        "created_on": created_on,
        "observed_on": observed_on,
        "unobserved_by_user_id": unobserved_by_user_id,
        "apply_project_rules_for": apply_project_rules_for,
        "cs": cs,
        "csa": csa,
        "csi": csi,
        "geoprivacy": geoprivacy,
        "taxon_geoprivacy": taxon_geoprivacy,
        "hrank": hrank or max_rank,
        "lrank": lrank or min_rank,
        "iconic_taxa": iconic_taxa,
        "id_above": id_above,
        "id_below": id_below,
        "identifications": identifications,
        "lat": lat,
        "lng": lng,
        "radius": radius,
        "nelat": nelat,
        "nelng": nelng,
        "swlat": swlat,
        "swlng": swlng,
        "list_id": list_id,
        "not_in_project": not_in_project,
        "not_matching_project_rules_for": not_matching_project_rules_for,
        "q": q,
        "search_on": search_on,
        "quality_grade": quality_grade,
        "updated_since": updated_since,
        "viewer_id": viewer_id,
        "reviewed": reviewed,
        "locale": locale,
        "preferred_place_id": preferred_place_id,
        "ttl": ttl,
        "user_agent": user_agent,
    }
    r = make_inaturalist_api_get_call("observations/species_counts", params=params)
    r.raise_for_status()
    return r.json()


# Update docstring with super long argument documentation
_returns = """
Returns:
    JSON containing observation counts, ordered by count descending
"""
docstrings.append(get_observation_species_counts, [docstrings.GET_OBSERVATIONS, _returns])


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


def get_places_nearby(
    nelat: float,
    nelng: float,
    swlat: float,
    swlng: float,
    name: str = None,
    user_agent: str = None,
) -> JsonResponse:
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

    Args:
        nelat: NE latitude of bounding box
        nelng: NE longitude of bounding box
        swlat: SW latitude of bounding box
        swlng: SW longitude of bounding box
        name: Name must match this value

    Returns:
        A list of dicts containing places results
    """
    r = make_inaturalist_api_get_call(
        "places/nearby",
        params={"nelat": nelat, "nelng": nelng, "swlat": swlat, "swlng": swlng, "name": name},
        user_agent=user_agent,
    )
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


def get_taxa(
    min_rank: str = None, max_rank: str = None, user_agent: str = None, **params
) -> JsonResponse:
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
    r = make_inaturalist_api_get_call("taxa", params=params, user_agent=user_agent)
    r.raise_for_status()
    return r.json()


def get_taxa_autocomplete(user_agent: str = None, minify: bool = False, **params) -> JsonResponse:
    """ Given a query string, returns taxa with names starting with the search term
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
    r = make_inaturalist_api_get_call("taxa/autocomplete", params=params, user_agent=user_agent)
    r.raise_for_status()
    json_response = r.json()

    if minify:
        json_response["results"] = [format_taxon(t) for t in json_response["results"]]
    return json_response
