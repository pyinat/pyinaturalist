# TODO: pprint examples are out of date
from copy import deepcopy
from logging import getLogger
from typing import Optional

from pyinaturalist.constants import (
    API_V1,
    V1_OBS_ORDER_BY_PROPERTIES,
    HistogramResponse,
    IntOrStr,
    JsonResponse,
    ListResponse,
    MultiFile,
    MultiInt,
    MultiIntOrStr,
    ResponseResult,
)
from pyinaturalist.converters import (
    convert_all_coordinates,
    convert_all_timestamps,
    convert_generic_timestamps,
    convert_histogram,
    convert_observation_histogram,
    convert_observation_timestamps,
    ensure_list,
)
from pyinaturalist.docs import document_common_args, document_request_params
from pyinaturalist.docs import templates as docs
from pyinaturalist.exceptions import ObservationNotFound
from pyinaturalist.paginator import paginate_all
from pyinaturalist.request_params import convert_observation_params, validate_multiple_choice_param
from pyinaturalist.session import delete, get, post, put

logger = getLogger(__name__)


@document_request_params(
    *docs._get_observations, docs._pagination, docs._only_id, docs._access_token
)
def get_observations(**params) -> JsonResponse:
    """Search observations

    .. rubric:: Notes

    * :fas:`lock-open` :ref:`Optional authentication <auth>` (For private/obscured coordinates)
    * API reference: :v1:`GET /observations <Observations/get_observations>`

    Examples:

        Get observations of Monarch butterflies with photos + public location info,
        on a specific date in the provice of Saskatchewan, CA (place ID 7953):

        >>> response = get_observations(
        >>>     taxon_name='Danaus plexippus',
        >>>     created_on='2020-08-27',
        >>>     photos=True,
        >>>     geo=True,
        >>>     geoprivacy='open',
        >>>     place_id=7953,
        >>> )

        Get basic info for observations in response:

        >>> pprint(response)
        '[57754375] Species: Danaus plexippus (Monarch) observed by samroom on 2020-08-27 at Railway Ave, Wilcox, SK'
        '[57707611] Species: Danaus plexippus (Monarch) observed by ingridt3 on 2020-08-26 at Michener Dr, Regina, SK'

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations_node.py

    Returns:
        Response dict containing observation records
    """
    params = validate_multiple_choice_param(params, 'order_by', V1_OBS_ORDER_BY_PROPERTIES)

    if params.get('page') == 'all':
        observations = paginate_all(get, f'{API_V1}/observations', method='id', **params)
    else:
        observations = get(f'{API_V1}/observations', **params).json()

    observations['results'] = convert_all_coordinates(observations['results'])
    observations['results'] = convert_all_timestamps(observations['results'])
    return observations


@document_common_args
def get_observations_by_id(
    observation_id: MultiInt, access_token: Optional[str] = None, **params
) -> JsonResponse:
    """Get one or more observations by ID

    .. rubric:: Notes

    * :fas:`lock-open` :ref:`Optional authentication <auth>` (For private/obscured coordinates)
    * API reference: :v1:`GET /observations/{id} <Observations/get_observations_id>`
    * This endpoint returns more complete annotation details compared to
      :py:func:`~pyinaturalist.v1.observations.get_observations`.
      See :py:class:`.Annotation` for details.

    Example:
        >>> response = get_observations_by_id(16227955)
        >>> response = get_observations_by_id([16227955, 16227956])

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations_by_id.py

    Args:
        observation_id: Get an observation with this ID. Multiple IDs are allowed.
        access_token: An access token, as returned by :py:func:`.get_access_token()`

    Returns:
        Response dict containing observation records
    """
    observations = get(
        f'{API_V1}/observations', ids=observation_id, access_token=access_token, **params
    ).json()
    observations['results'] = convert_all_coordinates(observations['results'])
    observations['results'] = convert_all_timestamps(observations['results'])
    return observations


@document_request_params(*docs._get_observations, docs._observation_histogram)
def get_observation_histogram(**params) -> HistogramResponse:
    """Search observations and return histogram data for the given time interval

    .. rubric:: Notes

    * API reference: :v1:`GET /observations/histogram <Observations/get_observations_histogram>`
    * Search parameters are the same as :py:func:`~pyinaturalist.v1.observations.get_observations()`,
      with the addition of ``date_field`` and ``interval``.
    * ``date_field`` may be either 'observed' (default) or 'created'.
    * Observed date ranges can be filtered by parameters ``d1`` and ``d2``
    * Created date ranges can be filtered by parameters ``created_d1`` and ``created_d2``
    * ``interval`` may be one of: 'year', 'month', 'week', 'day', 'hour', 'month_of_year', or
      'week_of_year'; spaces are also allowed instead of underscores, e.g. 'month of year'.
    * The year, month, week, day, and hour interval options will set default values for ``d1`` and
      ``created_d1``, to limit the number of groups returned. You can override those values if you
      want data from a longer or shorter time span.
    * The 'hour' interval only works with ``date_field='created'``

    Example:
        Get observations per month during 2020 in Austria (place ID 8057)

        >>> response = get_observation_histogram(
        >>>     interval='month',
        >>>     d1='2020-01-01',
        >>>     d2='2020-12-31',
        >>>     place_id=8057,
        >>> )

        .. admonition:: Example Response (observations per month of year)
            :class: toggle

            .. literalinclude:: ../sample_data/get_observation_histogram_month_of_year.py

        .. admonition:: Example Response (observations per month)
            :class: toggle

            .. literalinclude:: ../sample_data/get_observation_histogram_month.py

        .. admonition:: Example Response (observations per day)
            :class: toggle

            .. literalinclude:: ../sample_data/get_observation_histogram_day.py

    Returns:
        Dict of ``{time_key: observation_count}``. Keys are ints for 'month of year' and\
        'week of year' intervals, and :py:class:`~datetime.datetime` objects for all other intervals.
    """
    response = get(f'{API_V1}/observations/histogram', **params)
    return convert_observation_histogram(response.json())


@document_request_params(*docs._get_observations, docs._pagination)
def get_observation_identifiers(**params) -> JsonResponse:
    """Get identifiers of observations matching the search criteria and the count of
    observations they have identified. By default, results are sorted by ID count in descending.

    .. rubric:: Notes

    * API reference: :v1:`GET /observations/identifiers <Observations/get_observations_identifiers>`
    * This endpoint will only return up to 500 results.

    Example:
        >>> response = get_observation_identifiers(place_id=72645)
        >>> pprint(response)
        [409010  ] jdoe42 (Jane Doe)
        [691216  ] jbrown252 (James Brown)
        [3959037 ] tnsparkleberry

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_observation_identifiers_ex_results.json
                :language: JSON

    Returns:
        Response dict of identifiers
    """
    params.setdefault('per_page', 500)
    response = get(f'{API_V1}/observations/identifiers', **params)
    return response.json()


@document_request_params(*docs._get_observations, docs._pagination)
def get_observation_observers(**params) -> JsonResponse:
    """Get observers of observations matching the search criteria and the count of
    observations and distinct taxa of rank species they have observed.

    .. rubric:: Notes

    * API reference: :v1:`GET /observations/observers <Observations/get_observations_observers>`
    * Options for ``order_by`` are 'observation_count' (default) or 'species_count'
    * This endpoint will only return up to 500 results
    * See this issue for more details: https://github.com/inaturalist/iNaturalistAPI/issues/235

    Example:
        >>> response = get_observation_observers(place_id=72645, order_by='species_count')
        >>> pprint(response)
        [1566366 ] fossa1211
        [674557  ] schurchin
        [5813    ] fluffberger (Fluff Berger)


        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_observation_observers_ex_results.json
                :language: JSON

    Returns:
        Response dict of observers
    """
    params.setdefault('per_page', 500)
    response = get(f'{API_V1}/observations/observers', **params)
    return response.json()


@document_request_params(*docs._get_observations, docs._pagination)
def get_observation_species_counts(**params) -> JsonResponse:
    """Get all species (or other 'leaf taxa') associated with observations matching the search
    criteria, and the count of observations they are associated with.
    **Leaf taxa** are the leaves of the taxonomic tree, e.g., species, subspecies, variety, etc.

    .. rubric:: Notes

    * API reference: :v1:`GET /observations/species_counts <Observations/get_observations_species_counts>`

    Example:
        >>> response = get_observation_species_counts(user_login='my_username', quality_grade='research')
        >>> pprint(response)
        [62060] Species: Palomena prasina (Green Shield Bug): 10
        [84804] Species: Graphosoma italicum (European Striped Shield Bug): 8
        [55727] Species: Cymbalaria muralis (Ivy-leaved toadflax): 3
        ...

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_observation_species_counts.py

    Returns:
        Response dict containing taxon records with counts
    """
    if params.get('page') == 'all':
        return paginate_all(get, f'{API_V1}/observations/species_counts', **params)
    else:
        return get(f'{API_V1}/observations/species_counts', **params).json()


@document_request_params(*docs._get_observations)
def get_observation_popular_field_values(**params) -> JsonResponse:
    """Get controlled terms values and a monthly histogram of observations matching the search

    .. rubric:: Notes

    * API reference: :v1:`GET /observations/popular_field_values <Observations/get_observations_popular_field_values>`

    Example:
        >>> response = get_observation_popular_field_values(
        ...     species_name='Danaus plexippus', place_id=24,
        ... )

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_observation_popular_field_values.py

    Returns:
        Response dict. Each record contains a ``count``, a ``month_of_year`` histogram, a
            ``controlled_attribute``, and a ``controlled_value``.
    """
    response_json = get(f'{API_V1}/observations/popular_field_values', **params).json()
    for r in response_json['results']:
        r['month_of_year'] = convert_histogram(r['month_of_year'], interval='month_of_year')
    return response_json


def get_observation_taxonomy(user_id: Optional[IntOrStr] = None, **params) -> JsonResponse:
    """Get observation counts for all taxa in a full taxonomic tree. In the web UI, these are used
    for life lists.

    Args:
        user_id: iNaturalist user ID or username

    Example:
        >>> response = get_observation_taxonomy(user_id='my_username')

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_observation_taxonomy.json
                :language: JSON

    Returns:
        Response dict containing taxon records with counts
    """
    if params.get('page') == 'all':
        return paginate_all(get, f'{API_V1}/observations/taxonomy', user_id=user_id, **params)
    else:
        return get(f'{API_V1}/observations/taxonomy', user_id=user_id, **params).json()


@document_common_args
def get_observation_taxon_summary(observation_id: int, **params) -> JsonResponse:
    """Get information about an observation's taxon, within the context of the observation's location

    .. rubric:: Notes

    * API reference: :v1:`GET /observations/{id}/taxon_summary <Observations/get_observations_id_taxon_summary>`

    Args:
        observation_id: Observation ID to get taxon summary for

    Example:
        >>> response = get_observation_taxon_summary(7849808)

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_observation_taxon_summary.py

    Returns:
        Response dict containing taxon summary, optionally with conservation status and listed taxon
    """
    results = get(f'{API_V1}/observations/{observation_id}/taxon_summary', **params).json()
    results['conservation_status'] == convert_generic_timestamps(results['conservation_status'])
    results['listed_taxon'] == convert_generic_timestamps(results['listed_taxon'])
    return results


@document_request_params(docs._access_token, docs._create_observation)
def create_observation(**params) -> JsonResponse:
    """Create or update a new observation.

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * API reference: :v1:`POST /observations <Observations/post_observations>`

    Example:
        >>> token = get_access_token()
        >>> # Create a new observation:
        >>> create_observation(
        ...     access_token=token,
        ...     species_guess='Pieris rapae',
        ...     photos='~/observation_photos/2020_09_01_14003156.jpg',
        ...     observation_fields={297: 1},  # 297 is the obs. field ID for 'Number of individuals'
        ... )
        >>>
        >>> # Update an existing observation:
        >>> create_observation(
        ...     access_token=token,
        ...     uuid='53411fc2-bdf0-434e-afce-4dac33970173',
        ...     description='Updated description!',
        ... )

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/create_observation_v1.json
                :language: JSON

    Returns:
        JSON response containing the newly created observation(s)
    """
    photos, sounds, photo_ids, params, kwargs = convert_observation_params(params)
    response = post(f'{API_V1}/observations', json={'observation': params}, **kwargs)
    response_json = response.json()
    observation_id = response_json['id']

    upload(observation_id, photos=photos, sounds=sounds, photo_ids=photo_ids, **kwargs)
    return response_json


@document_request_params(
    docs._observation_id,
    docs._access_token,
    docs._create_observation,
)
def update_observation(observation_id: int, **params) -> ListResponse:
    """Update a single observation

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * API reference: :v1:`PUT /observations <Observations/put_observations>`

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
    """
    photos, sounds, photo_ids, params, kwargs = convert_observation_params(params)
    payload = {'observation': params}

    # If adding photos by ID, they must be appended to the list of existing photo IDs
    if photo_ids:
        logger.info(f'Adding {len(photo_ids)} existing photos')
        obs = get_observation(observation_id)
        combined_photo_ids = [p['id'] for p in obs['photos']]
        combined_photo_ids.extend(ensure_list(photo_ids))
        payload['local_photos'] = {str(observation_id): combined_photo_ids}
        kwargs.pop('ignore_photos', None)

    response = put(f'{API_V1}/observations/{observation_id}', json=payload, **kwargs)
    upload(observation_id, photos=photos, sounds=sounds, **kwargs)
    return response.json()


@document_common_args
def upload(
    observation_id: int,
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
    * API reference: :v1:`POST /observation_photos <Observation_Photos/post_observation_photos>`

    Example:

        >>> token = get_access_token()
        >>> upload(
        ...     1234,
        ...     photos=['~/observations/2020_09_01_140031.jpg', '~/observations/2020_09_01_140042.jpg'],
        ...     sounds='~/observations/2020_09_01_140031.mp3',
        ...     photo_ids=[1234, 5678],
        ...     access_token=token,
        ... )

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/upload_photos_and_sounds.json
                :language: JSON

    Args:
        observation_id: the ID of the observation
        photos: One or more image files, file-like objects, file paths, or URLs
        sounds: One or more audio files, file-like objects, file paths, or URLs
        photo_ids: One or more IDs of previously uploaded photos to attach to the observation
        access_token: Access token for user authentication, as returned by :func:`get_access_token()`

    Returns:
        Information about the uploaded file(s)
    """
    params['raise_for_status'] = False
    responses = []
    photos, sounds = ensure_list(photos), ensure_list(sounds)
    logger.info(f'Uploading {len(photos)} photos and {len(sounds)} sounds')

    # Upload photos
    photo_params = deepcopy(params)
    photo_params['observation_photo[observation_id]'] = observation_id
    for photo in photos:
        response = post(f'{API_V1}/observation_photos', files=photo, **photo_params)
        responses.append(response)

    # Upload sounds
    sound_params = deepcopy(params)
    sound_params['observation_sound[observation_id]'] = observation_id
    for sound in sounds:
        response = post(f'{API_V1}/observation_sounds', files=sound, **sound_params)
        responses.append(response)

    # Attach previously uploaded photos by ID
    if photo_ids:
        response = update_observation(
            observation_id, photo_ids=photo_ids, access_token=params.get('access_token', None)
        )
        responses.append(response)

    # Wait until all uploads complete to raise errors for any failed uploads
    for response in responses:
        response.raise_for_status()
    return [response.json() for response in responses]


@document_request_params(docs._observation_id, docs._access_token)
def delete_observation(observation_id: int, access_token: Optional[str] = None, **params):
    """Delete an observation

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * API reference: :v1:`DELETE /observations/{id} <Observations/delete_observations_id>`

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
        f'{API_V1}/observations/{observation_id}',
        access_token=access_token,
        raise_for_status=False,
        **params,
    )
    if response.status_code == 404:
        raise ObservationNotFound
    response.raise_for_status()


@document_common_args
def get_observation(
    observation_id: int, access_token: Optional[str] = None, **params
) -> ResponseResult:
    """Get details about a single observation by ID

    .. rubric:: Notes

    * :fas:`triangle-exclamation` Deprecated; use :func:`get_observations`
      or :func:`get_observations_by_id` instead
    * :fas:`lock-opens` :ref:`Optional authentication <auth>` (For private/obscured coordinates)
    * API reference: :v1:`GET /observations/{id} <Observations/get_observations_id>`

    Example:
        >>> response = get_observation(16227955)

    Args:
        observation_id: Get the observation with this ID. Only a single value is allowed.
        access_token: An access token, as returned by :py:func:`.get_access_token()`

    Returns:
        A dict with details on the observation

    Raises:
        :py:exc:`.ObservationNotFound` If an invalid observation is specified
    """

    response = get_observations(id=observation_id, access_token=access_token, **params)
    if response['results']:
        return convert_observation_timestamps(response['results'][0])
    raise ObservationNotFound()
