# Code to access the (read-only, but fast) Node based public iNaturalist API
# See: http://api.inaturalist.org/v1/docs/
from logging import getLogger
from time import sleep
from typing import Dict, Any, List

import requests
from urllib.parse import urljoin

from pyinaturalist.constants import THROTTLING_DELAY, INAT_NODE_API_BASE_URL, RANKS
from pyinaturalist.exceptions import ObservationNotFound
from pyinaturalist.helpers import is_int, merge_two_dicts
from pyinaturalist.api_requests import get

PER_PAGE_RESULTS = 30  # Paginated queries: how many records do we ask per page?

logger = getLogger(__name__)


def make_inaturalist_api_get_call(
    endpoint: str, params: Dict, user_agent: str = None, **kwargs
) -> requests.Response:
    """Make an API call to iNaturalist.

    endpoint is a string such as 'observations'
    method: 'GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE'
    kwargs are passed to requests.request
    Returns a requests.Response object
    """
    response = get(
        urljoin(INAT_NODE_API_BASE_URL, endpoint),
        params=params,
        user_agent=user_agent,
        **kwargs
    )
    return response


def get_observation(observation_id: int, user_agent: str = None) -> Dict[str, Any]:
    """Get details about an observation.

    :param observation_id:
    :param user_agent: a user-agent string that will be passed to iNaturalist.

    :returns: a dict with details on the observation
    :raises: ObservationNotFound
    """

    r = get_observations(params={"id": observation_id}, user_agent=user_agent)
    if r["results"]:
        return r["results"][0]

    raise ObservationNotFound()


def get_observations(params: Dict, user_agent: str = None) -> Dict[str, Any]:
    """Search observations, see: http://api.inaturalist.org/v1/docs/#!/Observations/get_observations.

    Returns the parsed JSON returned by iNaturalist (observations in r['results'], a list of dicts)
    """

    r = make_inaturalist_api_get_call(
        "observations", params=params, user_agent=user_agent
    )
    return r.json()


def get_all_observations(params: Dict, user_agent: str = None) -> List[Dict[str, Any]]:
    """Like get_observations() but handles pagination so you get all the results in one shot.

    Some params will be overwritten: order_by, order, per_page, id_above (do NOT specify page when using this).

    Returns a list of dicts (one entry per observation)
    """

    # According to the doc: "The large size of the observations index prevents us from supporting the page parameter
    # when retrieving records from large result sets. If you need to retrieve large numbers of records, use the
    # per_page and id_above or id_below parameters instead.

    results = []  # type: List[Dict[str, Any]]
    id_above = 0

    while True:
        iteration_params = merge_two_dicts(
            params,
            {
                "order_by": "id",
                "order": "asc",
                "per_page": PER_PAGE_RESULTS,
                "id_above": id_above,
            },
        )

        page_obs = get_observations(params=iteration_params, user_agent=user_agent)
        results = results + page_obs["results"]

        if page_obs["total_results"] <= PER_PAGE_RESULTS:
            return results

        sleep(THROTTLING_DELAY)
        id_above = results[-1]["id"]


def get_taxa_by_id(taxon_id: int, user_agent: str = None) -> Dict[str, Any]:
    """
    Get one or more taxa by ID.
    See: https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa_id

    :param: taxon_id: Get taxa with this ID. Multiple values are allowed.

    :returns: A list of dicts containing taxa results
    """
    if not is_int(taxon_id):
        raise ValueError("Please specify a single integer for the taxon ID")
    r = make_inaturalist_api_get_call(
        "taxa/{}".format(taxon_id), {}, user_agent=user_agent
    )
    r.raise_for_status()
    return r.json()


def get_taxa(
    user_agent: str = None, min_rank: str = None, max_rank: str = None, **params
) -> Dict[str, Any]:
    """Given zero to many of following parameters, returns taxa matching the search criteria.
    See https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa

    :param q: Name must begin with this value
    :param is_active: Taxon is active
    :param taxon_id: Only show taxa with this ID, or its descendants
    :param parent_id: Taxon's parent must have this ID
    :param rank: Taxon must have this exact rank
    :param min_rank: Taxon must have this rank or higher; overrides ``rank``
    :param max_rank: Taxon must have this rank or lower; overrides ``rank``
    :param rank_level: Taxon must have this rank level. Some example values are 70 (kingdom),
        60 (phylum), 50 (class), 40 (order), 30 (family), 20 (genus), 10 (species), 5 (subspecies)
    :param id_above: Must have an ID above this value
    :param id_below: Must have an ID below this value
    :param per_page: Number of results to return in a page. The maximum value is generally 200
        unless otherwise noted
    :param locale: Locale preference for taxon common names
    :param preferred_place_id: Place preference for regional taxon common names
    :param only_id: Return only the record IDs
    :param all_names: Include all taxon names in the response

    :returns: A list of dicts containing taxa results
    """
    if min_rank or max_rank:
        params["rank"] = _get_rank_range(min_rank, max_rank)
    r = make_inaturalist_api_get_call("taxa", params, user_agent=user_agent)
    r.raise_for_status()
    return r.json()


def get_taxa_autocomplete(
    user_agent: str = None, minify: bool = False, **params
) -> Dict[str, Any]:
    """Given a query string, returns taxa with names starting with the search term
    See: https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa_autocomplete

    **Note:** There appears to currently be a bug in the API that causes ``per_page`` to not have
    any effect.

    :param q: Name must begin with this value
    :param is_active: Taxon is active
    :param taxon_id: Only show taxa with this ID, or its descendants
    :param rank: Taxon must have this rank
    :param rank_level: Taxon must have this rank level. Some example values are 70 (kingdom),
        60 (phylum), 50 (class), 40 (order), 30 (family), 20 (genus), 10 (species), 5 (subspecies)
    :param per_page: Number of results to return in a page. The maximum value is generally 200 unless otherwise noted
    :param locale: Locale preference for taxon common names
    :param preferred_place_id: Place preference for regional taxon common names
    :param all_names: Include all taxon names in the response
    :param minify: Condense each match into a single string containg taxon ID, rank, and name

    :returns: A list of dicts containing taxa results
    """
    r = make_inaturalist_api_get_call(
        "taxa/autocomplete", params, user_agent=user_agent
    )
    r.raise_for_status()
    json_response = r.json()

    if minify:
        json_response["results"] = [format_taxon(t) for t in json_response["results"]]
    return json_response


def format_taxon(taxon: Dict) -> str:
    """Format a taxon result into a single string containing taxon ID, rank, and name
    (including common name, if available).
    """
    # Visually align taxon IDs (< 7 chars) and ranks (< 11 chars)
    common = taxon.get("preferred_common_name")
    return "{:>8}: {:>12} {}{}".format(
        taxon["id"],
        taxon["rank"].title(),
        taxon["name"],
        " ({})".format(common) if common else "",
    )


def _get_rank_range(min_rank: str = None, max_rank: str = None) -> List[str]:
    """ Translate min and/or max rank into a list of ranks """
    min_rank_index = _get_rank_index(min_rank) if min_rank else 0
    max_rank_index = _get_rank_index(max_rank) + 1 if max_rank else len(RANKS)
    return RANKS[min_rank_index:max_rank_index]


def _get_rank_index(rank: str) -> int:
    if rank not in RANKS:
        raise ValueError("Invalid rank")
    return RANKS.index(rank)
