"""
Code to access the (read-only, but fast) Node based public iNaturalist API
See: http://api.inaturalist.org/v1/docs/

Most recent API version tested: 1.3.0
"""
from logging import getLogger
from time import sleep
from typing import Dict, List

import requests
from urllib.parse import urljoin

from pyinaturalist.api_docs import (
    get_observations_params,
    get_all_observations_params,
    get_observation_species_counts_params,
    get_geojson_observations_params,
    get_places_nearby_params,
    get_projects_params,
    get_taxa_params,
    get_taxa_autocomplete_params,
)
from pyinaturalist.constants import (
    INAT_NODE_API_BASE_URL,
    PER_PAGE_RESULTS,
    THROTTLING_DELAY,
    MultiInt,
    JsonResponse,
)
from pyinaturalist.exceptions import ObservationNotFound
from pyinaturalist.forge_utils import document_request_params
from pyinaturalist.request_params import (
    DEFAULT_OBSERVATION_ATTRS,
    NODE_OBS_ORDER_BY_PROPERTIES,
    PROJECT_ORDER_BY_PROPERTIES,
    check_deprecated_params,
    translate_rank_range,
    validate_multiple_choice_param,
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


# Observations
# --------------------


def get_observation(observation_id: int, user_agent: str = None) -> JsonResponse:
    """Get details about an observation.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Observations/get_observations_id

    Example:

        >>> get_observation(16227955)

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_observation.json
                :language: JSON

    Args:
        observation_id: Observation ID
        user_agent: a user-agent string that will be passed to iNaturalist.

    Returns:
        A dict with details on the observation

    Raises:
        :py:exc:`.ObservationNotFound`
    """

    r = get_observations(id=observation_id, user_agent=user_agent)
    if r["results"]:
        return r["results"][0]

    raise ObservationNotFound()


# TODO: Example + sample response
@document_request_params(get_observations_params)
def get_observations(params: Dict = None, user_agent: str = None, **kwargs) -> JsonResponse:
    """Search observations.

    **API reference:** http://api.inaturalist.org/v1/docs/#!/Observations/get_observations

    Returns:
        JSON response containing observation records
    """
    kwargs = check_deprecated_params(params, **kwargs)
    validate_multiple_choice_param(kwargs, "order_by", NODE_OBS_ORDER_BY_PROPERTIES)
    r = make_inaturalist_api_get_call("observations", params=kwargs, user_agent=user_agent)
    return r.json()


# TODO: Example + sample response
@document_request_params(get_all_observations_params)
def get_all_observations(
    params: Dict = None, user_agent: str = None, **kwargs
) -> List[JsonResponse]:
    """Like :py:func:`get_observations()`, but handles pagination and returns all results in one
    call. Explicit pagination parameters will be ignored.

    Notes on pagination from the iNaturalist documentation:
    "The large size of the observations index prevents us from supporting the page parameter when
    retrieving records from large result sets. If you need to retrieve large numbers of records,
    use the ``per_page`` and ``id_above`` or ``id_below`` parameters instead."

    Returns:
        Combined list of observation records
    """
    kwargs = check_deprecated_params(params, **kwargs)
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
    """Get all species (or other "leaf taxa") associated with observations matching the search
    criteria, and the count of observations they are associated with.
    **Leaf taxa** are the leaves of the taxonomic tree, e.g., species, subspecies, variety, etc.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Observations/get_observations_species_counts

    Example:
        >>> get_observation_species_counts(user_login='my_username', quality_grade='research')

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_observation_species_counts.json
                :language: JSON

    Returns:
        JSON response containing taxon records with counts
    """
    r = make_inaturalist_api_get_call(
        "observations/species_counts",
        params=kwargs,
        user_agent=user_agent,
    )
    r.raise_for_status()
    return r.json()


@document_request_params(get_geojson_observations_params)
def get_geojson_observations(properties: List[str] = None, **kwargs) -> JsonResponse:
    """Get all observation results combined into a GeoJSON ``FeatureCollection``.
    By default this includes some basic observation properties as GeoJSON ``Feature`` properties.
    The ``properties`` argument can be used to override these defaults.

    Example:
        >>> get_geojson_observations(observation_id=16227955, properties=["photo_url"])

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations.geojson
                :language: JSON

    Returns:
        A ``FeatureCollection`` containing observation results as ``Feature`` dicts.
    """
    kwargs["mappable"] = True
    observations = get_all_observations(**kwargs)
    return as_geojson_feature_collection(
        (flatten_nested_params(obs) for obs in observations),
        properties=properties if properties is not None else DEFAULT_OBSERVATION_ATTRS,
    )


# Places
# --------------------

# TODO: Use updated sample responses with converted coords


def _convert_all_locations_to_float(response):
    """ Convert locations for both standard (curated) and community-contributed places to floats """
    response["results"] = {
        "standard": convert_location_to_float(response["results"].get("standard")),
        "community": convert_location_to_float(response["results"].get("community")),
    }
    return response


def get_places_by_id(place_id: MultiInt, user_agent: str = None) -> JsonResponse:
    """
    Get one or more places by ID.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Places/get_places_id

    Example:
        >>> get_places_by_id([93735, 89191])

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_places_by_id.json
                :language: JSON

    Args:
        place_id: Get a place with this ID. Multiple values are allowed.

    Returns:
        JSON response containing place records
    """
    r = make_inaturalist_api_get_call("places", ids=place_id, user_agent=user_agent)
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

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Places/get_places_nearby

    Example:
        >>> bounding_box = (150.0, -50.0, -149.999, -49.999)
        >>> get_places_nearby(*bounding_box)

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_places_nearby.json
                :language: JSON

    Returns:
        JSON response containing place records
    """
    r = make_inaturalist_api_get_call("places/nearby", params=kwargs, user_agent=user_agent)
    r.raise_for_status()
    return _convert_all_locations_to_float(r.json())


def get_places_autocomplete(q: str, user_agent: str = None) -> JsonResponse:
    """Given a query string, get places with names starting with the search term

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Places/get_places_autocomplete

    Example:
        >>> get_places_autocomplete('Irkutsk')

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_places_autocomplete.json
                :language: JSON

    Args:
        q: Name must begin with this value

    Returns:
        JSON response containing place records
    """
    r = make_inaturalist_api_get_call("places/autocomplete", params={"q": q}, user_agent=user_agent)
    r.raise_for_status()

    # Convert coordinates to floats
    response = r.json()
    response["results"] = convert_location_to_float(response["results"])
    return response


# Projects
# --------------------


@document_request_params(get_projects_params)
def get_projects(user_agent: str = None, **kwargs) -> JsonResponse:
    """Given zero to many of following parameters, get projects matching the search criteria.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Projects/get_projects

    Example:

        Search for projects about invasive species within 400km of Vancouver, BC:

        >>> response = get_projects(
        >>>     q='invasive',
        >>>     lat=49.27,
        >>>     lng=-123.08,
        >>>     radius=400,
        >>>     order_by='distance',
        >>> )

        Show basic info for projects in response:

        >>> project_info = {p["id"]: p["title"] for p in response["results"]}
        >>> print('\\n'.join([f'{k}:\\t{v}' for k, v in project_info.items()]))
        8291:    PNW Invasive Plant EDDR
        19200:   King County (WA) Noxious and Invasive Weeds
        8527:    WA Invasives
        2344:    Invasive & Huntable Animals
        6432:    CBWN Invasive Plants

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_projects.json
                :language: JSON

    Returns:
        JSON response containing project records
    """
    validate_multiple_choice_param(kwargs, "order_by", PROJECT_ORDER_BY_PROPERTIES)
    r = make_inaturalist_api_get_call("projects", params=kwargs, user_agent=user_agent)
    r.raise_for_status()

    # Convert coordinates to floats
    response = r.json()
    response["results"] = convert_location_to_float(response["results"])
    return response


def get_projects_by_id(
    project_id: MultiInt, rule_details: bool = None, user_agent: str = None
) -> JsonResponse:
    """Get one or more projects by ID.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Projects/get_projects_id

    Example:

        >>> get_projects_by_id([8348, 6432])

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_projects_by_id.json
                :language: JSON

    Args:
        project_id: Get projects with this ID. Multiple values are allowed.
        rule_details: Return more information about project rules, for example return a full taxon
            object instead of simply an ID

    Returns:
        JSON response containing project records
    """
    r = make_inaturalist_api_get_call(
        "projects",
        ids=project_id,
        params={"rule_details": rule_details},
        user_agent=user_agent,
    )
    r.raise_for_status()

    # Convert coordinates to floats
    response = r.json()
    response["results"] = convert_location_to_float(response["results"])
    return response


# Taxa
# --------------------


@document_request_params(get_taxa_params)
def get_taxa(user_agent: str = None, **kwargs) -> JsonResponse:
    """Given zero to many of following parameters, get taxa matching the search criteria.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa

    Example:

        >>> response = get_taxa(q="vespi", rank=["genus", "family"])
        >>> print({taxon["id"]: taxon["name"] for taxon in response["results"]})
        {52747: "Vespidae", 84737: "Vespina", 92786: "Vespicula", 646195: "Vespiodes", ...}

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_taxa.json
                :language: JSON

    Returns:
        JSON response containing taxon records
    """
    kwargs = translate_rank_range(kwargs)
    r = make_inaturalist_api_get_call("taxa", params=kwargs, user_agent=user_agent)
    r.raise_for_status()
    return r.json()


def get_taxa_by_id(taxon_id: MultiInt, user_agent: str = None) -> JsonResponse:
    """Get one or more taxa by ID.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa_id

    Example:

        >>> response = get_taxa_by_id(343248)
        >>> basic_fields = ["preferred_common_name", "observations_count", "wikipedia_url", "wikipedia_summary"]
        >>> print({f: response["results"][0][f] for f in basic_fields})
        {
            "preferred_common_name": "Paper Wasps",
            "observations_count": 69728,
            "wikipedia_url": "http://en.wikipedia.org/wiki/Polistinae",
            "wikipedia_summary": "The Polistinae are eusocial wasps closely related to the more familiar yellow jackets...",
        }

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_taxa_by_id.json
                :language: JSON

    Args:
        taxon_id: Get taxa with this ID. Multiple values are allowed.

    Returns:
        JSON response containing taxon records
    """
    r = make_inaturalist_api_get_call("taxa", ids=taxon_id, user_agent=user_agent)
    r.raise_for_status()
    return r.json()


@document_request_params(get_taxa_autocomplete_params)
def get_taxa_autocomplete(user_agent: str = None, **kwargs) -> JsonResponse:
    """Given a query string, returns taxa with names starting with the search term

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa_autocomplete

    **Note:** There appears to currently be a bug in the API that causes ``per_page`` to not have
    any effect.

    Example:

        >>> response = get_taxa_autocomplete(q='vespi')
        >>> first_result = response['results'][0]
        >>> print(first_result['rank'], first_result['name'])
        'family Vespidae'

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_taxa_autocomplete.json
                :language: JSON

        .. admonition:: Example Response (with **minify=True**)
            :class: toggle

            .. literalinclude:: ../sample_data/get_taxa_autocomplete_minified.json
                :language: JSON

    Returns:
        JSON response containing taxon records
    """
    kwargs = translate_rank_range(kwargs)
    r = make_inaturalist_api_get_call("taxa/autocomplete", params=kwargs, user_agent=user_agent)
    r.raise_for_status()
    json_response = r.json()

    if kwargs.get("minify"):
        json_response["results"] = [format_taxon(t) for t in json_response["results"]]
    return json_response
