from copy import deepcopy
from logging import getLogger

from pyinaturalist.constants import API_V2, V2_OBS_ORDER_BY_PROPERTIES, JsonResponse, RequestParams
from pyinaturalist.converters import convert_all_coordinates, convert_all_timestamps
from pyinaturalist.docs import document_request_params
from pyinaturalist.docs import templates as docs
from pyinaturalist.paginator import paginate_all
from pyinaturalist.request_params import validate_multiple_choice_param
from pyinaturalist.session import get, post

logger = getLogger(__name__)


# TODO: Send GET request with RISON if it fits in URL character limit?
# TODO: Code reuse, cleanup, etc.
@document_request_params(
    *docs._get_observations,
    docs._observation_v2,
    docs._pagination,
    docs._only_id,
    docs._access_token,
)
def get_observations(**params) -> JsonResponse:
    """Search observations

    .. rubric:: Notes

    * :fas:`lock-open` :ref:`Optional authentication <auth>` (For private/obscured coordinates)
    * API reference: :v2:`GET /observations <Observations/get_observations>`
    * See `iNaturalist API v2 documentation <https://api.inaturalist.org/v2/docs>`_ for details on
      selecting return fields using ``fields`` parameter
    * :fa:`exclamation-triangle` **Provisional:** This is for testing purposes only, and will change in future releases

    Examples:

        Get observations of Monarch butterflies with photos + public location info,
        on a specific date in the province of Saskatchewan, CA (place ID 7953),
        and return all available fields:

        >>> response = get_observations(
        >>>     taxon_name='Danaus plexippus',
        >>>     created_on='2020-08-27',
        >>>     photos=True,
        >>>     geo=True,
        >>>     geoprivacy='open',
        >>>     place_id=7953,
        >>>     fields='all',
        >>> )

        Get basic info for observations in response:

        >>> pprint(response)
        '[57754375] Species: Danaus plexippus (Monarch) observed by samroom on 2020-08-27 at Railway Ave, Wilcox, SK'
        '[57707611] Species: Danaus plexippus (Monarch) observed by ingridt3 on 2020-08-26 at Michener Dr, Regina, SK'

        Return all response fields *except* identifications:

        >>> response = get_observations(id=14150125, except_fields=['identifications'])

        Search for observations with a given observation field:

        >>> response = get_observations(observation_fields=['Species count'])

        Or observation field value:

        >>> response = get_observations(observation_fields={'Species count': 2})

        .. dropdown:: Example Response (default/minimal)
            :color: primary
            :icon: code-square

            .. literalinclude:: ../sample_data/get_observations_v2_minimal.py

        .. dropdown:: Example Response (all fields)
            :color: primary
            :icon: code-square

            .. literalinclude:: ../sample_data/get_observations_v2_full.py

    Returns:
        Response dict containing observation records
    """
    params = validate_multiple_choice_param(params, 'order_by', V2_OBS_ORDER_BY_PROPERTIES)
    except_fields = params.pop('except_fields', None)

    if params.get('fields') and except_fields:
        raise ValueError('Cannot use both fields and except_fields')

    # Request all fields except those specified
    if except_fields:
        params['fields'] = deepcopy(ALL_OBS_FIELDS)
        for k in except_fields:
            params['fields'].pop(k, None)

    # If no field selections are specified (or all fields), use GET method
    if params.get('fields') in ['all', None]:
        observations = _get_observations(params)

    # If field selections are specified, use POST method and put fields in request body
    else:
        observations = _get_post_observations(params)

    observations['results'] = convert_all_coordinates(observations['results'])
    observations['results'] = convert_all_timestamps(observations['results'])
    return observations


def _get_observations(params: RequestParams) -> JsonResponse:
    if params.get('page') == 'all':
        return paginate_all(get, f'{API_V2}/observations', method='id', **params)
    else:
        return get(f'{API_V2}/observations', **params).json()


def _get_post_observations(params: RequestParams) -> JsonResponse:
    """Use POST method to get observations with selection of return fields.
    This allows for more complex requests that may exceed the max length of a GET URL.
    """
    headers = {'X-HTTP-Method-Override': 'GET'}
    fields = {'fields': params.pop('fields')}

    if params.get('page') == 'all':
        return paginate_all(
            post,
            f'{API_V2}/observations',
            method='id',
            headers=headers,
            json=fields,
            **params,
        )
    else:
        return post(
            f'{API_V2}/observations',
            headers=headers,
            json=fields,
            **params,
        ).json()


# The full `fields` value to request all observation details
ALL_OBS_FIELDS = {
    "annotations": {
        "controlled_attribute": {"id": True, "label": True, "multivalued": True},
        "controlled_value": {"id": True, "label": True, "multivalued": True},
        "user": {"login": True, "icon_url": True},
        "vote_score": True,
        "votes": {"vote_flag": True, "user": {"login": True, "icon_url": True}},
    },
    "application": {"icon": True, "name": True, "url": True},
    "comments": {
        "body": True,
        "created_at": True,
        "flags": {"id": True},
        "hidden": True,
        "id": True,
        "moderator_actions": {
            "action": True,
            "id": True,
            "created_at": True,
            "reason": True,
            "user": {"login": True, "icon_url": True},
        },
        "spam": True,
        "user": {"login": True, "icon_url": True},
    },
    "community_taxon": {
        "ancestry": True,
        "ancestor_ids": True,
        "ancestors": {
            "id": True,
            "uuid": True,
            "name": True,
            "iconic_taxon_name": True,
            "is_active": True,
            "preferred_common_name": True,
            "rank": True,
            "rank_level": True,
        },
        "default_photo": {
            "attribution": True,
            "license_code": True,
            "url": True,
            "square_url": True,
        },
        "iconic_taxon_name": True,
        "id": True,
        "is_active": True,
        "name": True,
        "preferred_common_name": True,
        "rank": True,
        "rank_level": True,
    },
    "created_at": True,
    "description": True,
    "faves": {"id": True, "user": {"login": True, "icon_url": True}},
    "flags": {"id": True, "flag": True, "resolved": True},
    "geojson": True,
    "geoprivacy": True,
    "id": True,
    "identifications": {
        "body": True,
        "category": True,
        "created_at": True,
        "current": True,
        "disagreement": True,
        "flags": {"id": True},
        "hidden": True,
        "moderator_actions": {
            "action": True,
            "id": True,
            "created_at": True,
            "reason": True,
            "user": {"login": True, "icon_url": True},
        },
        "previous_observation_taxon": {
            "ancestry": True,
            "ancestor_ids": True,
            "ancestors": {
                "id": True,
                "uuid": True,
                "name": True,
                "iconic_taxon_name": True,
                "is_active": True,
                "preferred_common_name": True,
                "rank": True,
                "rank_level": True,
            },
            "default_photo": {
                "attribution": True,
                "license_code": True,
                "url": True,
                "square_url": True,
            },
            "iconic_taxon_name": True,
            "id": True,
            "is_active": True,
            "name": True,
            "preferred_common_name": True,
            "rank": True,
            "rank_level": True,
        },
        "spam": True,
        "taxon": {
            "ancestry": True,
            "ancestor_ids": True,
            "ancestors": {
                "id": True,
                "uuid": True,
                "name": True,
                "iconic_taxon_name": True,
                "is_active": True,
                "preferred_common_name": True,
                "rank": True,
                "rank_level": True,
            },
            "default_photo": {
                "attribution": True,
                "license_code": True,
                "url": True,
                "square_url": True,
            },
            "iconic_taxon_name": True,
            "id": True,
            "is_active": True,
            "name": True,
            "preferred_common_name": True,
            "rank": True,
            "rank_level": True,
        },
        "taxon_change": {"id": True, "type": True},
        "updated_at": True,
        "user": {"login": True, "icon_url": True, "id": True},
        "uuid": True,
        "vision": True,
    },
    "identifications_most_agree": True,
    "latitude": True,
    "license_code": True,
    "location": True,
    "longitude": True,
    "map_scale": True,
    "non_traditional_projects": {
        "current_user_is_member": True,
        "project_user": {"user": {"login": True, "icon_url": True}},
        "project": {
            "admins": {"user_id": True},
            "icon": True,
            "project_observation_fields": {
                "id": True,
                "observation_field": {
                    "allowed_values": True,
                    "datatype": True,
                    "description": True,
                    "id": True,
                    "name": True,
                },
            },
            "slug": True,
            "title": True,
        },
    },
    "obscured": True,
    "observed_on": True,
    "observed_time_zone": True,
    "ofvs": {
        "observation_field": {
            "allowed_values": True,
            "datatype": True,
            "description": True,
            "name": True,
            "taxon": {"name": True},
            "uuid": True,
        },
        "user": {"login": True, "icon_url": True},
        "uuid": True,
        "value": True,
        "taxon": {
            "ancestry": True,
            "ancestor_ids": True,
            "ancestors": {
                "id": True,
                "uuid": True,
                "name": True,
                "iconic_taxon_name": True,
                "is_active": True,
                "preferred_common_name": True,
                "rank": True,
                "rank_level": True,
            },
            "default_photo": {
                "attribution": True,
                "license_code": True,
                "url": True,
                "square_url": True,
            },
            "iconic_taxon_name": True,
            "id": True,
            "is_active": True,
            "name": True,
            "preferred_common_name": True,
            "rank": True,
            "rank_level": True,
        },
    },
    "outlinks": {"source": True, "url": True},
    "photos": {
        "id": True,
        "uuid": True,
        "url": True,
        "license_code": True,
        "flags": {"id": True, "flag": True, "resolved": True},
    },
    "place_guess": True,
    "place_ids": True,
    "positional_accuracy": True,
    "preferences": {"prefers_community_taxon": True},
    "private_geojson": True,
    "private_place_guess": True,
    "private_place_ids": True,
    "project_observations": {
        "current_user_is_member": True,
        "preferences": {"allows_curator_coordinate_access": True},
        "project": {
            "admins": {"user_id": True},
            "icon": True,
            "project_observation_fields": {
                "id": True,
                "observation_field": {
                    "allowed_values": True,
                    "datatype": True,
                    "description": True,
                    "id": True,
                    "name": True,
                },
            },
            "slug": True,
            "title": True,
        },
        "uuid": True,
    },
    "public_positional_accuracy": True,
    "quality_grade": True,
    "reviewed_by": True,
    "sounds": {
        "file_url": True,
        "file_content_type": True,
        "id": True,
        "license_code": True,
        "play_local": True,
        "url": True,
        "uuid": True,
    },
    "tags": True,
    "taxon": {
        "ancestry": True,
        "ancestor_ids": True,
        "ancestors": {
            "id": True,
            "uuid": True,
            "name": True,
            "iconic_taxon_name": True,
            "is_active": True,
            "preferred_common_name": True,
            "rank": True,
            "rank_level": True,
        },
        "default_photo": {
            "attribution": True,
            "license_code": True,
            "url": True,
            "square_url": True,
        },
        "iconic_taxon_name": True,
        "id": True,
        "is_active": True,
        "name": True,
        "preferred_common_name": True,
        "rank": True,
        "rank_level": True,
    },
    "taxon_geoprivacy": True,
    "time_observed_at": True,
    "time_zone": True,
    "user": {
        "login": True,
        "icon_url": True,
        "id": True,
        "name": True,
        "observations_count": True,
        "preferences": {
            "prefers_community_taxa": True,
            "prefers_observation_fields_by": True,
            "prefers_project_addition_by": True,
        },
    },
    "viewer_trusted_by_observer": True,
    "votes": {
        "id": True,
        "user": {"login": True, "icon_url": True, "id": True},
        "vote_flag": True,
        "vote_scope": True,
    },
}
