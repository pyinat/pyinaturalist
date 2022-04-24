"""
Functions to access the iNaturalist API v1
See: http://api.inaturalist.org/v1/docs/

Most recent API version tested: 1.3.0
"""
# flake8: noqa: F401, F403
from requests import Response

from pyinaturalist.constants import API_V1_BASE_URL
from pyinaturalist.session import delete, get, post, put


def get_v1(endpoint: str, **kwargs) -> Response:
    """Make a GET request to iNaturalist API v1"""
    return get(f'{API_V1_BASE_URL}/{endpoint}', **kwargs)


def post_v1(endpoint: str, **kwargs) -> Response:
    """Make a POST request to iNaturalist API v1"""
    return post(f'{API_V1_BASE_URL}/{endpoint}', **kwargs)


def put_v1(endpoint: str, **kwargs) -> Response:
    """Make a PUT request to iNaturalist API v1"""
    return put(f'{API_V1_BASE_URL}/{endpoint}', **kwargs)


def delete_v1(endpoint: str, **kwargs) -> Response:
    """Make a DELETE request to iNaturalist API v1"""
    return delete(f'{API_V1_BASE_URL}/{endpoint}', **kwargs)


from pyinaturalist.v1.controlled_terms import get_controlled_terms
from pyinaturalist.v1.identifications import get_identifications, get_identifications_by_id
from pyinaturalist.v1.messages import get_message_by_id, get_messages, get_unread_meassage_count
from pyinaturalist.v1.observation_fields import delete_observation_field, set_observation_field
from pyinaturalist.v1.observations import (
    create_observation,
    delete_observation,
    get_observation,
    get_observation_histogram,
    get_observation_identifiers,
    get_observation_observers,
    get_observation_popular_field_values,
    get_observation_species_counts,
    get_observation_taxon_summary,
    get_observation_taxonomy,
    get_observations,
    update_observation,
    upload,
)
from pyinaturalist.v1.places import get_places_autocomplete, get_places_by_id, get_places_nearby
from pyinaturalist.v1.posts import get_posts
from pyinaturalist.v1.projects import (
    add_project_observation,
    add_project_users,
    delete_project_observation,
    delete_project_users,
    get_projects,
    get_projects_by_id,
    update_project,
)
from pyinaturalist.v1.search import search
from pyinaturalist.v1.taxa import (
    get_taxa,
    get_taxa_autocomplete,
    get_taxa_by_id,
    get_taxa_map_layers,
)
from pyinaturalist.v1.users import get_user_by_id, get_users_autocomplete
