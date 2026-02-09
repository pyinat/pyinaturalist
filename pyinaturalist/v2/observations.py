from copy import deepcopy
from logging import getLogger
from typing import Any, Dict, List, Optional

from pyinaturalist.constants import (
    API_V2,
    V2_OBS_ORDER_BY_PROPERTIES,
    JsonResponse,
    ListResponse,
    MultiFile,
    MultiIntOrStr,
    RequestParams,
)
from pyinaturalist.converters import convert_all_coordinates, convert_all_timestamps, ensure_list
from pyinaturalist.docs import document_common_args, document_request_params
from pyinaturalist.docs import templates as docs
from pyinaturalist.exceptions import ObservationNotFound
from pyinaturalist.paginator import paginate_all
from pyinaturalist.request_params import convert_observation_params, validate_multiple_choice_param
from pyinaturalist.session import delete, get, post, put

logger = getLogger(__name__)


# TODO: Send GET request with RISON if it fits in URL character limit?
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

    * :fas:`lock-open` :ref:`Optional authentication <auth>` For private/obscured coordinates
      and original filenames
    * :fa:`exclamation-triangle` **Provisional:** v2 endpoints are still in development, and may
      change in future releases
    * API reference: :v2:`GET /observations <Observations/get_observations>`
    * See `iNaturalist API v2 documentation <https://api.inaturalist.org/v2/docs>`_ for details on
      selecting return fields using ``fields`` parameter

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

        Return only observation UUIDs and users:

        >>> response = get_observations(
        >>>     taxon_name='Danaus plexippus',
        >>>     created_on='2020-08-27',
        >>>     fields={'uuid':True, 'user':{'login':True}},
        >>> )

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

    # If field selections are specified, or we're querying more IDs than can fit in a GET request,
    # then use POST method and put field selection + other params in request body
    n_ids = len(ensure_list(params.get('id')))
    if params.get('fields') not in ['all', None] or n_ids > 30:
        observations = _get_post_observations(params)
    # Otherwise use GET method
    else:
        observations = _get_observations(params)

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
    body = params
    params = {k: body.pop(k) for k in ['page', 'per_page'] if k in body}
    if params.get('page') == 'all':
        return paginate_all(
            post,
            f'{API_V2}/observations',
            method='id',
            headers=headers,
            json=body,
            **params,
        )
    else:
        return post(f'{API_V2}/observations', headers=headers, json=body, **params).json()


@document_common_args
def upload(
    observation_uuid: str,
    photos: Optional[MultiFile] = None,
    sounds: Optional[MultiFile] = None,
    photo_ids: Optional[MultiIntOrStr] = None,
    **params,
) -> ListResponse:
    """Upload one or more local photo and/or sound files, and add them to an existing observation.

    You may also attach a previously uploaded photo by photo ID, e.g. if your photo contains
    multiple organisms and you want to create a separate observation for each one.

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * :fa:`exclamation-triangle` **Provisional:** v2 endpoints are still in development, and may
      change in future releases
    * API reference: :v2:`POST /observation_photos <ObservationPhotos/post_observation_photos>`
    * API reference: :v2:`POST /observation_sounds <ObservationSounds/post_observation_sounds>`

    Example:

        >>> token = get_access_token()
        >>> upload(
        ...     '53411fc2-bdf0-434e-afce-4dac33970173',
        ...     photos=['~/observations/2020_09_01_140031.jpg', '~/observations/2020_09_01_140042.jpg'],
        ...     sounds='~/observations/2020_09_01_140031.mp3',
        ...     photo_ids=[1234, 5678],
        ...     access_token=token,
        ... )

        .. dropdown:: Example Response
            :color: primary
            :icon: code-square


            .. code-block:: javascript

                [{"id": 178539}, {"id": 955963}]

    Args:
        observation_uuid: The UUID of the observation
        photos: One or more image files, file-like objects, file paths, or URLs
        sounds: One or more audio files, file-like objects, file paths, or URLs
        photo_ids: One or more IDs of previously uploaded photos to attach to the observation
        access_token: Access token for user authentication, as returned by :func:`get_access_token()`

    Returns:
        IDs only for newly created files
    """
    params['raise_for_status'] = False
    responses = []
    photos, sounds = ensure_list(photos), ensure_list(sounds)
    logger.info(f'Uploading {len(photos)} photos and {len(sounds)} sounds')

    # Upload photos
    photo_data = {'observation_photo[observation_id]': observation_uuid}
    for photo in photos:
        response = post(f'{API_V2}/observation_photos', files=photo, data=photo_data, **params)
        responses.append(response)

    # Upload sounds
    sound_data = {'observation_sound[observation_id]': observation_uuid}
    for sound in sounds:
        response = post(f'{API_V2}/observation_sounds', files=sound, data=sound_data, **params)
        responses.append(response)

    # Attach previously uploaded photos by ID
    # Note: API will return a 422 if photo ID is invalid or has already been added to the observation
    if photo_ids:
        logger.info(f'Attaching {len(ensure_list(photo_ids))} existing photos')
        for photo_id in ensure_list(photo_ids):
            payload = {
                'observation_photo': {
                    'observation_id': observation_uuid,
                    'photo_id': int(photo_id),
                }
            }
            response = post(f'{API_V2}/observation_photos', json=payload, **params)
            responses.append(response)

    # Wait until all uploads complete to raise errors for any failed uploads
    for response in responses:
        response.raise_for_status()
    return [response.json()['results'][0] for response in responses]


@document_request_params(docs._access_token, docs._create_observation, docs._create_observation_v2)
def create_observation(**params) -> JsonResponse:
    """Create a new observation.

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * :fa:`exclamation-triangle` **Provisional:** v2 endpoints are still in development, and may
      change in future releases
    * API reference: :v2:`POST /observations <Observations/post_observations>`

    Example:
        >>> token = get_access_token()
        >>> # Create a new observation:
        >>> create_observation(
        ...     access_token=token,
        ...     species_guess='Pieris rapae',
        ...     observed_on='2020-09-01',
        ...     photos='~/observation_photos/2020_09_01_14003156.jpg',
        ...     observation_fields={
        ...         297: 3,  # 297 is the obs. field ID for 'Number of individuals'
        ...         816: 1,  # 816 = 'Number of males'
        ...         821: 2,  # 821 = 'Number of females'
        ...     },
        ... )

        .. dropdown:: Example Response
            :color: primary
            :icon: code-square

            .. literalinclude:: ../sample_data/create_observation_v2.json
                :language: JSON

    Returns:
        JSON response containing the newly created observation (submitted fields only)
    """
    photos, sounds, photo_ids, params, kwargs = convert_observation_params(params)
    obs_fields: List[Dict] = params.pop('observation_field_values_attributes', [])

    response = post(f'{API_V2}/observations', json={'observation': params}, **kwargs)
    response_json = response.json()
    observation_uuid = response_json['results'][0]['uuid']

    # Set observation fields separately (v2 API doesn't allow multiple values)
    for obs_field in obs_fields:
        set_observation_field(observation_uuid, **obs_field, **kwargs)
    # Upload photos and sounds if provided
    if photos or sounds or photo_ids:
        upload(observation_uuid, photos=photos, sounds=sounds, photo_ids=photo_ids, **kwargs)

    return response_json['results'][0]


@document_request_params(
    docs._access_token,
    docs._create_observation,
    docs._create_observation_v2,
)
def update_observation(observation_uuid: str, **params) -> JsonResponse:
    """Update a single observation

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * :fa:`exclamation-triangle` **Provisional:** v2 endpoints are still in development, and may
      change in future releases
    * API reference: :v2:`PUT /observations/{uuid} <Observations/put_observations_uuid>`

    Example:

        >>> token = get_access_token()
        >>> update_observation(
        >>>     '53411fc2-bdf0-434e-afce-4dac33970173',
        >>>     access_token=token,
        >>>     description='updated description!',
        >>>     captive_flag=True,
        >>> )

        .. dropdown:: Example Response
            :color: primary
            :icon: code-square

            .. code-block:: javascript

                {"uuid": "6444ede0-9831-47bd-8c3b-ee32e08cbfe4"}

    Args:
        observation_uuid: UUID of the observation to update

    Returns:
        JSON response containing the updated observation
    """
    photos, sounds, photo_ids, params, kwargs = convert_observation_params(params)
    obs_fields: List[Dict] = params.pop('observation_field_values_attributes', [])
    payload = {'observation': params}

    response = put(f'{API_V2}/observations/{observation_uuid}', json=payload, **kwargs)

    # Set observation fields separately (v2 API doesn't allow multiple values)
    for obs_field in obs_fields:
        set_observation_field(observation_uuid, **obs_field, **kwargs)
    # Upload photos and sounds if provided
    if photos or sounds or photo_ids:
        upload(observation_uuid, photos=photos, sounds=sounds, photo_ids=photo_ids, **kwargs)

    return response.json()['results'][0]


@document_request_params(docs._access_token)
def delete_observation(observation_uuid: str, access_token: Optional[str] = None, **params):
    """Delete an observation

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * :fa:`exclamation-triangle` **Provisional:** v2 endpoints are still in development, and may
      change in future releases
    * API reference: :v2:`DELETE /observations/{uuid} <Observations/delete_observations_uuid>`

    Example:
        >>> token = get_access_token()
        >>> delete_observation('53411fc2-bdf0-434e-afce-4dac33970173', token)

    Args:
        observation_uuid: UUID of the observation to delete

    Returns:
        If successful, no response is returned from this endpoint

    Raises:
        :py:exc:`.ObservationNotFound` if the requested observation doesn't exist
        :py:exc:`requests.HTTPError` (403) if the observation belongs to another user
    """
    response = delete(
        f'{API_V2}/observations/{observation_uuid}',
        access_token=access_token,
        raise_for_status=False,
        **params,
    )
    if response.status_code == 404:
        raise ObservationNotFound(response=response)
    response.raise_for_status()


@document_request_params(docs._access_token)
def set_observation_field(
    observation_id: int, observation_field_id: int, value: Any, **params
) -> JsonResponse:
    """Create or update an observation field value on an observation

    Args:
        observation_id: ID or UUID of the observation to update
        observation_field_id: ID of the observation field for this observation field value
        value: Value for the observation field

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * API reference: :v2:`POST /observation_field_values/{id} <ObservationFieldValues/post_observation_field_values>`
    * To find an ``observation_field_id``, either user :py:func:`.get_observation_fields` or
      `search observation fields on iNaturalist <https://www.inaturalist.org/observation_fields>`_

    Example:
        >>> set_observation_field(
        ...     7345179,
        ...     observation_field_id,
        ...     value=250,
        ...     access_token=token,
        ... )

        .. dropdown:: Example Response
            :color: primary
            :icon: code-square

            .. literalinclude:: ../sample_data/post_put_observation_field_value.json
                :language: javascript

    Returns:
        The newly updated field value record
    """
    body = {
        'observation_field_value': {
            'observation_id': observation_id,
            'observation_field_id': observation_field_id,
            'value': value,
        }
    }
    response = post(f'{API_V2}/observation_field_values', json=body, **params)
    return response.json()


# The full `fields` value to request all observation details
ALL_OBS_FIELDS = {
    'annotations': {
        'controlled_attribute': {'id': True, 'label': True},
        'controlled_value': {'id': True, 'label': True},
        'user': {'login': True, 'icon_url': True},
        'vote_score': True,
        'votes': {'user': {'login': True, 'icon_url': True}, 'vote_flag': True, 'vote_scope': True},
    },
    'application': {'icon': True, 'name': True, 'url': True},
    'captive': True,
    'comments': {
        'body': True,
        'created_at': True,
        'flags': {'id': True, 'comment': True},
        'hidden': True,
        'id': True,
        'moderator_actions': {
            'action': True,
            'id': True,
            'created_at': True,
            'reason': True,
            'user': {'login': True, 'icon_url': True},
        },
        'spam': True,
        'updated_at': True,
        'user': {'login': True, 'icon_url': True},
    },
    'community_taxon': {
        'ancestry': True,
        'ancestor_ids': True,
        'ancestors': {
            'id': True,
            'uuid': True,
            'name': True,
            'iconic_taxon_name': True,
            'is_active': True,
            'preferred_common_name': True,
            'rank': True,
            'rank_level': True,
        },
        'default_photo': {
            'attribution': True,
            'license_code': True,
            'url': True,
            'square_url': True,
        },
        'iconic_taxon_name': True,
        'id': True,
        'is_active': True,
        'name': True,
        'preferred_common_name': True,
        'rank': True,
        'rank_level': True,
    },
    'created_at': True,
    'description': True,
    'faves': {'created_at': True, 'id': True, 'user': {'login': True, 'icon_url': True}},
    'flags': {'id': True, 'comment': True, 'flag': True, 'resolved': True},
    'geojson': True,
    'geoprivacy': True,
    'id': True,
    'identifications': {
        'body': True,
        'category': True,
        'created_at': True,
        'current': True,
        'disagreement': True,
        'flags': {'id': True, 'comment': True, 'flag': True, 'resolved': True},
        'hidden': True,
        'moderator_actions': {
            'action': True,
            'id': True,
            'created_at': True,
            'reason': True,
            'user': {'login': True, 'icon_url': True},
        },
        'previous_observation_taxon': {
            'ancestry': True,
            'ancestor_ids': True,
            'ancestors': {
                'id': True,
                'uuid': True,
                'name': True,
                'iconic_taxon_name': True,
                'is_active': True,
                'preferred_common_name': True,
                'rank': True,
                'rank_level': True,
            },
            'default_photo': {
                'attribution': True,
                'license_code': True,
                'url': True,
                'square_url': True,
            },
            'iconic_taxon_name': True,
            'id': True,
            'is_active': True,
            'name': True,
            'preferred_common_name': True,
            'rank': True,
            'rank_level': True,
        },
        'spam': True,
        'taxon': {
            'ancestry': True,
            'ancestor_ids': True,
            'ancestors': {
                'id': True,
                'uuid': True,
                'name': True,
                'iconic_taxon_name': True,
                'is_active': True,
                'preferred_common_name': True,
                'rank': True,
                'rank_level': True,
            },
            'default_photo': {
                'attribution': True,
                'license_code': True,
                'url': True,
                'square_url': True,
            },
            'iconic_taxon_name': True,
            'id': True,
            'is_active': True,
            'name': True,
            'preferred_common_name': True,
            'rank': True,
            'rank_level': True,
        },
        'taxon_change': {'id': True, 'type': True},
        'updated_at': True,
        'user': {'login': True, 'icon_url': True, 'id': True},
        'uuid': True,
        'vision': True,
    },
    'identifications_most_agree': True,
    'license_code': True,
    'location': True,
    'map_scale': True,
    'mappable': True,
    'non_traditional_projects': {
        'current_user_is_member': True,
        'project_user': {'user': {'login': True, 'icon_url': True}},
        'project': {
            'admins': {'user_id': True},
            'icon': True,
            'project_observation_fields': {
                'id': True,
                'observation_field': {
                    'allowed_values': True,
                    'datatype': True,
                    'description': True,
                    'id': True,
                    'name': True,
                },
            },
            'slug': True,
            'title': True,
        },
    },
    'obscured': True,
    'observed_on': True,
    'observed_time_zone': True,
    'ofvs': {
        'observation_field': {
            'allowed_values': True,
            'datatype': True,
            'description': True,
            'name': True,
            'taxon': {'name': True},
            'uuid': True,
        },
        'user': {'login': True, 'icon_url': True},
        'uuid': True,
        'value': True,
        'taxon': {
            'ancestry': True,
            'ancestor_ids': True,
            'ancestors': {
                'id': True,
                'uuid': True,
                'name': True,
                'iconic_taxon_name': True,
                'is_active': True,
                'preferred_common_name': True,
                'rank': True,
                'rank_level': True,
            },
            'default_photo': {
                'attribution': True,
                'license_code': True,
                'url': True,
                'square_url': True,
            },
            'iconic_taxon_name': True,
            'id': True,
            'is_active': True,
            'name': True,
            'preferred_common_name': True,
            'rank': True,
            'rank_level': True,
        },
    },
    'out_of_range': True,
    'outlinks': {'source': True, 'url': True},
    'owners_identification_from_vision': True,
    'photos': {
        'id': True,
        'license_code': True,
        'original_dimensions': {'height': True, 'width': True},
        'original_filename': True,
        'flags': {'id': True, 'comment': True, 'flag': True, 'resolved': True},
        'type': True,
        'url': True,
    },
    'place_guess': True,
    'place_ids': True,
    'positional_accuracy': True,
    'preferences': {'auto_obscuration': True, 'prefers_community_taxon': True},
    'private_geojson': {'coordinates': True, 'type': True},
    'private_place_guess': True,
    'private_place_ids': True,
    'project_observations': {
        'current_user_is_member': True,
        'preferences': {'allows_curator_coordinate_access': True},
        'project': {
            'admins': {'user_id': True},
            'icon': True,
            'id': True,
            'project_observation_fields': {
                'id': True,
                'observation_field': {
                    'allowed_values': True,
                    'datatype': True,
                    'description': True,
                    'id': True,
                    'name': True,
                },
            },
            'slug': True,
            'title': True,
        },
        'uuid': True,
    },
    'public_positional_accuracy': True,
    'quality_grade': True,
    'quality_metrics': {
        'agree': True,
        'id': True,
        'metric': True,
        'user': {'login': True, 'icon_url': True},
    },
    'reviewed_by': True,
    'sounds': {
        'file_url': True,
        'file_content_type': True,
        'id': True,
        'license_code': True,
        'play_local': True,
        'original_filename': True,
    },
    'tags': True,
    'taxon': {
        'ancestry': True,
        'ancestor_ids': True,
        'ancestors': {
            'id': True,
            'uuid': True,
            'name': True,
            'iconic_taxon_name': True,
            'is_active': True,
            'preferred_common_name': True,
            'rank': True,
            'rank_level': True,
        },
        'default_photo': {
            'attribution': True,
            'license_code': True,
            'url': True,
            'square_url': True,
        },
        'iconic_taxon_name': True,
        'id': True,
        'is_active': True,
        'name': True,
        'preferred_common_name': True,
        'rank': True,
        'rank_level': True,
    },
    'taxon_geoprivacy': True,
    'time_observed_at': True,
    'time_zone': True,
    'user': {
        'login': True,
        'icon_url': True,
        'id': True,
        'name': True,
        'observations_count': True,
        'preferences': {
            'prefers_community_taxa': True,
            'prefers_observation_fields_by': True,
            'prefers_project_addition_by': True,
        },
    },
    'viewer_trusted_by_observer': True,
    'votes': {
        'created_at': True,
        'id': True,
        'user': {'login': True, 'icon_url': True, 'id': True},
        'vote_flag': True,
        'vote_scope': True,
    },
}
