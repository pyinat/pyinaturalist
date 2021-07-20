"""
Functions to access the iNaturalist API v1
See: http://api.inaturalist.org/v1/docs/

Most recent API version tested: 1.3.0
"""
# flake8: noqa: F401, F403
from requests import Response

from pyinaturalist.api_requests import get
from pyinaturalist.constants import API_V1_BASE_URL


def get_v1(endpoint: str, **kwargs) -> Response:
    """Make an API call to iNaturalist.

    Args:
        endpoint: The name of an endpoint resource, not including the base URL e.g. 'observations'
        kwargs: Arguments for :py:func:`.api_requests.request`
    """
    return get(f'{API_V1_BASE_URL}/{endpoint}', **kwargs)


from pyinaturalist.v1.controlled_terms import get_controlled_terms
from pyinaturalist.v1.identifications import get_identifications, get_identifications_by_id
from pyinaturalist.v1.observations import (
    get_observation,
    get_observation_histogram,
    get_observation_identifiers,
    get_observation_observers,
    get_observation_species_counts,
    get_observation_taxonomy,
    get_observations,
)
from pyinaturalist.v1.places import get_places_autocomplete, get_places_by_id, get_places_nearby
from pyinaturalist.v1.posts import get_posts
from pyinaturalist.v1.projects import get_projects, get_projects_by_id
from pyinaturalist.v1.search import search
from pyinaturalist.v1.taxa import get_taxa, get_taxa_autocomplete, get_taxa_by_id
from pyinaturalist.v1.users import get_user_by_id, get_users_autocomplete
