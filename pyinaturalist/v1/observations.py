from typing import List

from pyinaturalist import api_docs as docs
from pyinaturalist.constants import (
    NODE_OBS_ORDER_BY_PROPERTIES,
    HistogramResponse,
    IntOrStr,
    JsonResponse,
)
from pyinaturalist.converters import (
    as_geojson_feature_collection,
    convert_all_coordinates,
    convert_all_timestamps,
    convert_observation_timestamps,
    format_histogram,
)
from pyinaturalist.exceptions import ObservationNotFound
from pyinaturalist.forge_utils import document_request_params
from pyinaturalist.pagination import add_paginate_all
from pyinaturalist.request_params import validate_multiple_choice_param
from pyinaturalist.v1 import get_v1

# Basic observation attributes to include by default in geojson responses
DEFAULT_OBSERVATION_ATTRS = [
    'id',
    'photo_url',
    'positional_accuracy',
    'quality_grade',
    'taxon_id',
    'taxon_name',
    'taxon_common_name',
    'time_observed_at',
    'uri',
]


def get_observation(observation_id: int, user_agent: str = None) -> JsonResponse:
    """Get details about a single observation by ID

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Observations/get_observations_id

    Example:

        >>> response = get_observation(16227955)
        >>> print(format_observations(response))
        [16227955] [493595] Species: Lixus bardanae observed on 2018-09-05 14:06:00+01:00 by niconoe at 54 rue des Badauds

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_observation.py

    Args:
        observation_id: Observation ID
        user_agent: a user-agent string that will be passed to iNaturalist.

    Returns:
        A dict with details on the observation

    Raises:
        :py:exc:`.ObservationNotFound` If an invalid observation is specified
    """

    response = get_observations(id=observation_id, user_agent=user_agent)
    if response['results']:
        return convert_observation_timestamps(response['results'][0])
    raise ObservationNotFound()


@document_request_params([*docs._get_observations, docs._observation_histogram])
def get_observation_histogram(**params) -> HistogramResponse:
    """Search observations and return histogram data for the given time interval

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Observations/get_observations_histogram

    **Notes:**

    * Search parameters are the same as :py:func:`.get_observations()`, with the addition of
      ``date_field`` and ``interval``.
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
    response = get_v1('observations/histogram', params=params)
    return format_histogram(response.json())


@document_request_params([*docs._get_observations, docs._pagination, docs._only_id])
@add_paginate_all(method='id')
def get_observations(**params) -> JsonResponse:
    """Search observations.

    **API reference:** http://api.inaturalist.org/v1/docs/#!/Observations/get_observations

    Example:

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

        >>> from pyinaturalist.formatters import format_observations
        >>> print(format_observations(response))
        '[57754375] Species: Danaus plexippus (Monarch) observed by samroom on 2020-08-27 at Railway Ave, Wilcox, SK'
        '[57707611] Species: Danaus plexippus (Monarch) observed by ingridt3 on 2020-08-26 at Michener Dr, Regina, SK'

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations_node.py

    Returns:
        Response dict containing observation records
    """
    validate_multiple_choice_param(params, 'order_by', NODE_OBS_ORDER_BY_PROPERTIES)
    response = get_v1('observations', params=params)

    observations = response.json()
    observations['results'] = convert_all_coordinates(observations['results'])
    observations['results'] = convert_all_timestamps(observations['results'])

    return observations


@document_request_params([*docs._get_observations, docs._pagination])
@add_paginate_all(method='page')
def get_observation_species_counts(**params) -> JsonResponse:
    """Get all species (or other 'leaf taxa') associated with observations matching the search
    criteria, and the count of observations they are associated with.
    **Leaf taxa** are the leaves of the taxonomic tree, e.g., species, subspecies, variety, etc.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Observations/get_observations_species_counts

    Example:
        >>> response = get_observation_species_counts(user_login='my_username', quality_grade='research')
        >>> print(format_species_counts(response))
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
    response = get_v1('observations/species_counts', params=params)
    return response.json()


# TODO: Deprecate this and move to pyinaturalist-convert
@document_request_params([*docs._get_observations, docs._geojson_properties])
def get_geojson_observations(properties: List[str] = None, **params) -> JsonResponse:
    """Get all observation results combined into a GeoJSON ``FeatureCollection``.
    By default this includes some basic observation properties as GeoJSON ``Feature`` properties.
    The ``properties`` argument can be used to override these defaults.

    Example:
        >>> get_geojson_observations(observation_id=16227955, properties=['photo_url'])

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations.geojson
                :language: JSON

    Returns:
        A ``FeatureCollection`` containing observation results as ``Feature`` dicts.
    """
    params['mappable'] = True
    params['page'] = 'all'
    response = get_observations(**params)
    return as_geojson_feature_collection(
        response['results'],
        properties=properties if properties is not None else DEFAULT_OBSERVATION_ATTRS,
    )


@document_request_params([*docs._get_observations, docs._pagination])
def get_observation_observers(**params) -> JsonResponse:
    """Get observers of observations matching the search criteria and the count of
    observations and distinct taxa of rank species they have observed.

    Notes:
        * Options for ``order_by`` are 'observation_count' (default) or 'species_count'
        * This endpoint will only return up to 500 results
        * See this issue for more details: https://github.com/inaturalist/iNaturalistAPI/issues/235

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Observations/get_observations_observers

    Example:
        >>> response = get_observation_observers(place_id=72645, order_by='species_count')
        >>> print(format_users(response, align=True))
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
    response = get_v1('observations/observers', params=params)
    return response.json()


@document_request_params([*docs._get_observations, docs._pagination])
def get_observation_identifiers(**params) -> JsonResponse:
    """Get identifiers of observations matching the search criteria and the count of
    observations they have identified. By default, results are sorted by ID count in descending.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Observations/get_observations_identifiers

    Note: This endpoint will only return up to 500 results.

    Example:
        >>> response = get_observation_identifiers(place_id=72645)
        >>> print(format_users(response, align=True))
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
    response = get_v1('observations/identifiers', params=params)
    return response.json()


@add_paginate_all(method='page')
def get_observation_taxonomy(user_id: IntOrStr, user_agent: str = None) -> JsonResponse:
    """Get observation counts for all taxa in a full taxonomic tree. In the web UI, these are used
    for life lists.

    Args:
        user_id: iNaturalist user ID or username

    Example:
        >>> response = get_observation_taxonomy(user_id='my_username')
        ...

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_observation_taxonomy.json
                :language: JSON

    Returns:
        Response dict containing taxon records with counts
    """
    response = get_v1('observations/taxonomy', params={'user_id': user_id}, user_agent=user_agent)
    return response.json()
