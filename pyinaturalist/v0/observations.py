from logging import getLogger
from typing import List, Union

from pyinaturalist.api_requests import delete, get, post, put
from pyinaturalist.constants import (
    API_V0_BASE_URL,
    OBSERVATION_FORMATS,
    REST_OBS_ORDER_BY_PROPERTIES,
    ListResponse,
    MultiFile,
)
from pyinaturalist.converters import (
    convert_all_coordinates,
    convert_all_timestamps,
    ensure_file_obj,
    ensure_list,
)
from pyinaturalist.docs import document_request_params
from pyinaturalist.docs import templates as docs
from pyinaturalist.exceptions import ObservationNotFound
from pyinaturalist.pagination import add_paginate_all
from pyinaturalist.request_params import convert_observation_fields, validate_multiple_choice_param

logger = getLogger(__name__)


@document_request_params(
    [
        docs._observation_common,
        docs._observation_rest_only,
        docs._bounding_box,
        docs._pagination,
    ]
)
@add_paginate_all(method='page')
def get_observations(**params) -> Union[List, str]:
    """Get observation data, optionally in an alternative format. Also see
    :py:func:`.get_geojson_observations` for GeoJSON format (not included here because it wraps
    a separate API endpoint).

    **API reference:** https://www.inaturalist.org/pages/api+reference#get-observations

    Example:

        >>> get_observations(id=45414404, converters='atom')

        .. admonition:: Example Response (atom)
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations.atom
                :language: xml

        .. admonition:: Example Response (csv)
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations.csv

        .. admonition:: Example Response (dwc)
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations.dwc
                :language: xml

        .. admonition:: Example Response (json)
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations.json
                :language: json

        .. admonition:: Example Response (kml)
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations.kml
                :language: xml

        .. admonition:: Example Response (widget)
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations.js
                :language: javascript

    Returns:
        Return type will be ``dict`` for the ``json`` response format, and ``str`` for all others.
    """
    response_format = params.pop('response_format', 'json')
    if response_format == 'geojson':
        raise ValueError('For geojson format, use pyinaturalist.v1.get_geojson_observations')
    if response_format not in OBSERVATION_FORMATS:
        raise ValueError('Invalid response format')
    validate_multiple_choice_param(params, 'order_by', REST_OBS_ORDER_BY_PROPERTIES)

    response = get(f'{API_V0_BASE_URL}/observations.{response_format}', **params)
    if response_format == 'json':
        observations = response.json()
        observations = convert_all_coordinates(observations)
        observations = convert_all_timestamps(observations)
        return observations
    else:
        return response.text


@document_request_params([docs._access_token, docs._create_observation])
def create_observation(access_token: str, **params) -> ListResponse:
    """Create a new observation.

    **API reference:** https://www.inaturalist.org/pages/api+reference#post-observations

    Example:
        >>> token = get_access_token()
        >>> create_observation(
        >>>     access_token=token,
        >>>     species_guess='Pieris rapae',
        >>>     local_photos='~/observation_photos/2020_09_01_14003156.jpg',
        >>>     observation_fields={297: 1},  # 297 is the obs. field ID for 'Number of individuals'
        >>> )

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/create_observation_result.json
                :language: javascript

        .. admonition:: Example Response (failure)
            :class: toggle

            .. literalinclude:: ../sample_data/create_observation_fail.json
                :language: javascript

    Returns:
        JSON response containing the newly created observation(s)

    Raises:
        :py:exc:`requests.HTTPError`, if the call is not successful. iNaturalist returns an
        error 422 (unprocessable entity) if it rejects the observation data (for example an
        observation date in the future or a latitude > 90. In that case the exception's
        ``response`` attribute gives more details about the errors.
    """

    params, photos, sounds, user_agent, session = _process_observation_params(params)
    response = post(
        url=f'{API_V0_BASE_URL}/observations.json',
        json={'observation': params},
        access_token=access_token,
        user_agent=user_agent,
        session=session,
    )
    response_json = response.json()
    observation_id = response_json[0]['id']

    if photos:
        upload_photos(observation_id, photos, access_token)
    if sounds:
        upload_sounds(observation_id, sounds, access_token)
    return response_json


@document_request_params(
    [
        docs._observation_id,
        docs._access_token,
        docs._create_observation,
        docs._update_observation,
    ]
)
def update_observation(observation_id: int, access_token: str, **params) -> ListResponse:
    """
    Update a single observation.

    **API reference:** https://www.inaturalist.org/pages/api+reference#put-observations-id

    .. note::

        Unlike the underlying REST API endpoint, this function will **not** delete any existing
        photos from your observation if not specified in ``local_photos``. If you want this to
        behave the same as the REST API and you do want to delete photos, call with
        ``ignore_photos=False``.

    Example:

        >>> token = get_access_token()
        >>> update_observation(
        >>>     17932425,
        >>>     access_token=token,
        >>>     description='updated description!',
        >>> )

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/update_observation_result.json
                :language: javascript

    Returns:
        JSON response containing the newly updated observation(s)

    Raises:
        :py:exc:`requests.HTTPError`, if the call is not successful. iNaturalist returns an
            error 410 if the observation doesn't exists or belongs to another user.
    """
    params, photos, sounds, user_agent, session = _process_observation_params(params)
    response = put(
        url=f'{API_V0_BASE_URL}/observations/{observation_id}.json',
        json={'observation': params},
        access_token=access_token,
        user_agent=user_agent,
        session=session,
    )

    if photos:
        upload_photos(observation_id, photos, access_token)
    if sounds:
        upload_sounds(observation_id, sounds, access_token)
    return response.json()


def _process_observation_params(params):
    params = convert_observation_fields(params)
    if params.get('observed_on'):
        params['observed_on_string'] = params.pop('observed_on')

    # Split out photos and sounds to upload separately
    photos = ensure_list(params.pop('local_photos', None))
    photos.extend(ensure_list(params.pop('photos', None)))  # Alias for 'local_photos'
    sounds = ensure_list(params.pop('sounds', None))

    # Note: this is the only Boolean parameter that's specified as an int
    if 'ignore_photos' in params:
        params['ignore_photos'] = int(params['ignore_photos'])
    else:
        params['ignore_photos'] = 1

    user_agent = params.pop('user_agent', None)
    session = params.pop('session', None)
    return params, photos, sounds, user_agent, session


def upload_photos(observation_id: int, photos: MultiFile, access_token: str, **params) -> ListResponse:
    """Upload a local photo and assign it to an existing observation.

    Example:

        >>> token = get_access_token()
        >>> upload_photos(1234, '~/observations/2020_09_01_14003156.jpg', access_token=token)

        Multiple photos can be uploaded at once:

        >>> upload_photos(
        >>>     1234,
        >>>     ['~/observations/2020_09_01_14003156.jpg', '~/observations/2020_09_01_14004223.jpg'],
        >>>     access_token=token,
        >>> )

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/post_observation_photos_list.json
                :language: javascript

    Args:
        observation_id: the ID of the observation
        photo: An image file, file-like object, or path
        access_token: the access token, as returned by :func:`get_access_token()`

    Returns:
        Information about the uploaded photo(s)
    """
    responses = []

    for photo in ensure_list(photos):
        response = post(
            url=f'{API_V0_BASE_URL}/observation_photos',
            access_token=access_token,
            files={'file': ensure_file_obj(photo)},
            raise_for_status=False,
            **{'observation_photo[observation_id]': observation_id},
            **params,
        )
        responses.append(response)

    # Wait until all uploads complete to raise errors for any failed uploads
    for response in responses:
        response.raise_for_status()
    return [response.json() for response in responses]


def upload_sounds(observation_id: int, sounds: MultiFile, access_token: str, **params) -> ListResponse:
    """Upload a local sound file and assign it to an existing observation.

    Example:

        >>> token = get_access_token()
        >>> upload_sounds(1234, '~/observations/2020_09_01_14003156.mp3', access_token=token)

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/post_observation_sounds_list.json
                :language: javascript

        Multiple sounds can be uploaded at once:

        >>> upload_sounds(
        >>>     1234,
        >>>     ['~/observations/2020_09_01_14003156.mp3', '~/observations/2020_09_01_14004223.wav'],
        >>>     access_token=token,
        >>> )

    Args:
        observation_id: the ID of the observation
        sound: An audio file, file-like object, or path
        access_token: the access token, as returned by :func:`get_access_token()`

    Returns:
        Information about the uploaded sound(s)
    """
    responses = []

    for sound in ensure_list(sounds):
        response = post(
            url=f'{API_V0_BASE_URL}/observation_sounds',
            access_token=access_token,
            files={'file': ensure_file_obj(sound)},
            raise_for_status=False,
            **{'observation_sound[observation_id]': observation_id},
            **params,
        )
        responses.append(response)

    # Wait until all uploads complete to raise errors for any failed uploads
    for response in responses:
        response.raise_for_status()
    return [response.json() for response in responses]


@document_request_params([docs._observation_id, docs._access_token])
def delete_observation(observation_id: int, access_token: str = None, **params):
    """
    Delete an observation.

    **API reference:** https://www.inaturalist.org/pages/api+reference#delete-observations-id

    Example:

        >>> token = get_access_token()
        >>> delete_observation(17932425, token)

    Returns:
        If successful, no response is returned from this endpoint

    Raises:
        :py:exc:`.ObservationNotFound` if the requested observation doesn't exist
        :py:exc:`requests.HTTPError` (403) if the observation belongs to another user
    """
    response = delete(
        url=f'{API_V0_BASE_URL}/observations/{observation_id}.json',
        access_token=access_token,
        raise_for_status=False,
        **params,
    )
    if response.status_code == 404:
        raise ObservationNotFound
    response.raise_for_status()
