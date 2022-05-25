from logging import getLogger
from typing import List, Union

from pyinaturalist.constants import (
    API_V0,
    OBSERVATION_FORMATS,
    V0_OBS_ORDER_BY_PROPERTIES,
    ListResponse,
    MultiFile,
)
from pyinaturalist.converters import convert_all_coordinates, convert_all_timestamps, ensure_list
from pyinaturalist.docs import document_request_params
from pyinaturalist.docs import templates as docs
from pyinaturalist.exceptions import ObservationNotFound
from pyinaturalist.request_params import convert_observation_params, validate_multiple_choice_param
from pyinaturalist.session import delete, get, post, put

logger = getLogger(__name__)


@document_request_params(
    docs._observation_common,
    docs._observation_v0,
    docs._bounding_box,
    docs._pagination,
)
def get_observations(**params) -> Union[List, str]:
    """Get observation data, optionally in an alternative format

    .. rubric:: Notes

    * API reference: :v0:`GET /observations <get-observations>`

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
    if response_format not in OBSERVATION_FORMATS:
        raise ValueError('Invalid response format')
    validate_multiple_choice_param(params, 'order_by', V0_OBS_ORDER_BY_PROPERTIES)

    response = get(f'{API_V0}/observations.{response_format}', **params)
    if response_format == 'json':
        observations = response.json()
        observations = convert_all_coordinates(observations)
        observations = convert_all_timestamps(observations)
        return observations
    else:
        return response.text


@document_request_params(docs._access_token, docs._create_observation)
def create_observation(**params) -> ListResponse:
    """Create a new observation

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * API reference: :v0:`POST /observations <post-observations>`

    Example:
        >>> token = get_access_token()
        >>> create_observation(
        >>>     access_token=token,
        >>>     species_guess='Pieris rapae',
        >>>     photos='~/observation_photos/2020_09_01_14003156.jpg',
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
        :py:exc:`~urllib3.exceptions.HTTPError`: If the call is not successful. The exception's ``response`` attribute gives more details about the errors.
    """
    photos, sounds, _, params, kwargs = convert_observation_params(params)
    response = post(
        url=f'{API_V0}/observations.json',
        json={'observation': params},
        **kwargs,
    )
    response_json = response.json()
    observation_id = response_json[0]['id']

    if photos:
        upload_photos(observation_id, photos, **kwargs)
    if sounds:
        upload_sounds(observation_id, sounds, **kwargs)
    return response_json


@document_request_params(
    docs._observation_id,
    docs._access_token,
    docs._create_observation,
    docs._update_observation,
)
def update_observation(observation_id: int, **params) -> ListResponse:
    """Update a single observation

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * API reference: :v0:`PUT /observations/{id} <put-observations-id>`

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
        JSON response containing the newly updated observation

    Raises:
        :py:exc:`~urllib3.exceptions.HTTPError`: if the call is not successful. iNaturalist returns an error 410 if the observation doesn't exists or belongs to another user.
    """
    photos, sounds, _, params, kwargs = convert_observation_params(params)
    response = put(
        url=f'{API_V0}/observations/{observation_id}.json',
        json={'observation': params},
        **kwargs,
    )

    if photos:
        upload_photos(observation_id, photos, **kwargs)
    if sounds:
        upload_sounds(observation_id, sounds, **kwargs)
    return response.json()


def upload_photos(observation_id: int, photos: MultiFile, **params) -> ListResponse:
    """Upload a local photo and assign it to an existing observation

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * API reference: :v0:`POST /observation_photos <post-observation_photos>`

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
        access_token: Access token for user authentication, as returned by :func:`get_access_token()`

    Returns:
        Information about the uploaded photo(s)
    """
    responses = []
    params['observation_photo[observation_id]'] = observation_id

    for photo in ensure_list(photos):
        response = post(
            url=f'{API_V0}/observation_photos',
            files=photo,
            raise_for_status=False,
            **params,
        )
        responses.append(response)

    # Wait until all uploads complete to raise errors for any failed uploads
    for response in responses:
        response.raise_for_status()
    return [response.json() for response in responses]


def upload_sounds(observation_id: int, sounds: MultiFile, **params) -> ListResponse:
    """Upload a local sound file and assign it to an existing observation

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`

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
        access_token: Access token for user authentication, as returned by :func:`get_access_token()`

    Returns:
        Information about the uploaded sound(s)
    """
    responses = []
    params['observation_sound[observation_id]'] = observation_id

    for sound in ensure_list(sounds):
        response = post(
            url=f'{API_V0}/observation_sounds',
            files=sound,
            raise_for_status=False,
            **params,
        )
        responses.append(response)

    # Wait until all uploads complete to raise errors for any failed uploads
    for response in responses:
        response.raise_for_status()
    return [response.json() for response in responses]


@document_request_params(docs._observation_id, docs._access_token)
def delete_observation(observation_id: int, **params):
    """
    Delete an observation

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * API reference: :v0:`DELETE /observations/{id} <delete-observations-id>`

    Example:
        >>> token = get_access_token()
        >>> delete_observation(17932425, token)

    Returns:
        If successful, no response is returned from this endpoint

    Raises:
        :py:exc:`.ObservationNotFound`: if the requested observation doesn't exist
        :py:exc:`~urllib3.exceptions.HTTPError`: 403 if the observation belongs to another user
    """
    response = delete(
        url=f'{API_V0}/observations/{observation_id}.json',
        raise_for_status=False,
        **params,
    )
    if response.status_code == 404:
        raise ObservationNotFound
    response.raise_for_status()
