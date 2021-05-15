"""
Code to access the Node-based iNaturalist API
See: http://api.inaturalist.org/v1/docs/

Most recent API version tested: 1.3.0

Functions
---------

.. automodsumm:: pyinaturalist.node_api
    :functions-only:
    :nosignatures:
    :skip: get_all_observations

"""
from logging import getLogger
from typing import List
from warnings import warn

import requests

from pyinaturalist import api_docs as docs
from pyinaturalist.api_requests import get
from pyinaturalist.constants import API_V1_BASE_URL, HistogramResponse, JsonResponse, MultiInt
from pyinaturalist.exceptions import ObservationNotFound, TaxonNotFound
from pyinaturalist.forge_utils import document_request_params
from pyinaturalist.pagination import add_paginate_all, paginate_all
from pyinaturalist.request_params import (
    DEFAULT_OBSERVATION_ATTRS,
    NODE_OBS_ORDER_BY_PROPERTIES,
    PROJECT_ORDER_BY_PROPERTIES,
    translate_rank_range,
    validate_multiple_choice_param,
)
from pyinaturalist.response_format import (
    as_geojson_feature_collection,
    convert_all_coordinates,
    convert_all_place_coordinates,
    convert_all_timestamps,
    convert_generic_timestamps,
    convert_observation_timestamps,
    format_histogram,
)

__all__ = [
    'get_controlled_terms',
    'get_identifications_by_id',
    'get_identifications',
    'get_observation',
    'get_observation_histogram',
    'get_observations',
    'get_observation_species_counts',
    'get_geojson_observations',
    'get_observation_observers',
    'get_observation_identifiers',
    'get_places_by_id',
    'get_places_nearby',
    'get_places_autocomplete',
    'get_projects',
    'get_projects_by_id',
    'get_taxa',
    'get_taxa_by_id',
    'get_taxa_autocomplete',
    'get_user_by_id',
    'get_users_autocomplete',
]
logger = getLogger(__name__)


def node_api_get(endpoint: str, **kwargs) -> requests.Response:
    """Make an API call to iNaturalist.

    Args:
        endpoint: The name of an endpoint resource, not including the base URL e.g. 'observations'
        kwargs: Arguments for :py:func:`.api_requests.request`
    """
    return get(f'{API_V1_BASE_URL}/{endpoint}', **kwargs)


# Controlled Terms
# --------------------


def get_controlled_terms(taxon_id: int = None, user_agent: str = None) -> JsonResponse:
    """List controlled terms and their possible values.
    A taxon ID can optionally be provided to show only terms that are valid for that taxon.
    Otherwise, all controlled terms will be returned.

    **API reference:**

    * https://api.inaturalist.org/v1/docs/#!/Controlled_Terms/get_controlled_terms
    * https://api.inaturalist.org/v1/docs/#!/Controlled_Terms/get_controlled_terms_for_taxon

    Example:

        >>> response = get_controlled_terms()
        >>> print(format_controlled_terms(response))
        1: Life Stage
            2: Adult
            3: Teneral
            4: Pupa
        ...

        .. admonition:: Example Response (all terms)
            :class: toggle

            .. literalinclude:: ../sample_data/get_controlled_terms.json
                :language: JSON

        .. admonition:: Example Response (for a specific taxon)
            :class: toggle

            .. literalinclude:: ../sample_data/get_controlled_terms_for_taxon.json
                :language: JSON
    Args:
        taxon_id: ID of taxon to get controlled terms for
        user_agent: a user-agent string that will be passed to iNaturalist.

    Returns:
        A dict containing details on controlled terms and their values

    Raises:
        :py:exc:`.TaxonNotFound` If an invalid taxon_id is specified
    """
    # This is actually two endpoints, but they are so similar it seems best to combine them
    endpoint = 'controlled_terms/for_taxon' if taxon_id else 'controlled_terms'
    response = node_api_get(endpoint, params={'taxon_id': taxon_id}, user_agent=user_agent)

    # controlled_terms/for_taxon returns a 422 if the specified taxon does not exist
    if response.status_code in (404, 422):
        raise TaxonNotFound
    response.raise_for_status()
    return response.json()


# Identifications
# --------------------


def get_identifications_by_id(identification_id: MultiInt, user_agent: str = None) -> JsonResponse:
    """Get one or more identification records by ID.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Identifications/get_identifications_id

    Example:

        >>> get_identifications_by_id(155554373)

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_identifications.py

    Args:
        identification_id: Get taxa with this ID. Multiple values are allowed.

    Returns:
        Response dict containing identification records
    """
    r = node_api_get('identifications', ids=identification_id, user_agent=user_agent)
    r.raise_for_status()

    identifications = r.json()
    identifications['results'] = convert_all_timestamps(identifications['results'])
    return identifications


@document_request_params([docs._identification_params, docs._pagination, docs._only_id])
@add_paginate_all(method='page')
def get_identifications(**params) -> JsonResponse:
    """Search identifications.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Identifications/get_identifications

    Example:

        Get all of your own species-level identifications:

        >>> response = get_identifications(user_login='my_username', rank='species')
        >>> print([f"{i['user']['login']}: {i['taxon_id']} ({i['category']})" for i in response['results']])
        [155043569] Species: 76465 (leading) added on 2021-02-15 10:46:27-06:00 by jkcook
        [153668189] Species: 76465 (supporting) added on 2021-02-06 17:43:37+00:00 by jkcook
        [147500725] Species: 1163860 (improving) added on 2020-12-24 23:52:30+00:00 by jkcook
        ...

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_identifications.py

    Returns:
        Response dict containing identification records
    """
    params = translate_rank_range(params)
    r = node_api_get('identifications', params=params)
    r.raise_for_status()

    identifications = r.json()
    identifications['results'] = convert_all_timestamps(identifications['results'])
    return identifications


# Observations
# --------------------


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

    r = get_observations(id=observation_id, user_agent=user_agent)
    if r['results']:
        return convert_observation_timestamps(r['results'][0])

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
    r = node_api_get('observations/histogram', params=params)
    r.raise_for_status()
    return format_histogram(r.json())


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
    r = node_api_get('observations', params=params)
    r.raise_for_status()

    observations = r.json()
    observations['results'] = convert_all_coordinates(observations['results'])
    observations['results'] = convert_all_timestamps(observations['results'])

    return observations


def get_all_observations(**params) -> List[JsonResponse]:
    """Deprecated; use ``get_observations(page='all')`` instead"""
    msg = "get_all_observations() is deprecated; please use get_observations(page='all') instead"
    warn(DeprecationWarning(msg))
    return paginate_all(get_observations, method='id', **params)['results']


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
    r = node_api_get(
        'observations/species_counts',
        params=params,
    )
    r.raise_for_status()
    return r.json()


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
        [ 1566366] fossa1211
        [  674557] schurchin
        [    5813] fluffberger (Fluff Berger)


        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_observation_observers_ex_results.json
                :language: JSON

    Returns:
        Response dict of observers
    """
    params.setdefault('per_page', 500)

    r = node_api_get(
        'observations/observers',
        params=params,
    )
    r.raise_for_status()
    return r.json()


@document_request_params([*docs._get_observations, docs._pagination])
def get_observation_identifiers(**params) -> JsonResponse:
    """Get identifiers of observations matching the search criteria and the count of
    observations they have identified. By default, results are sorted by ID count in descending.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Observations/get_observations_identifiers

    Note: This endpoint will only return up to 500 results.

    Example:
        >>> response = get_observation_identifiers(place_id=72645)
        >>> print(format_users(response, align=True))
        [  409010] jdoe42 (Jane Doe)
        [  691216] jbrown252 (James Brown)
        [ 3959037] tnsparkleberry

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_observation_identifiers_ex_results.json
                :language: JSON

    Returns:
        Response dict of identifiers
    """
    params.setdefault('per_page', 500)

    r = node_api_get(
        'observations/identifiers',
        params=params,
    )
    r.raise_for_status()
    return r.json()


# Places
# --------------------


def get_places_by_id(place_id: MultiInt, user_agent: str = None) -> JsonResponse:
    """
    Get one or more places by ID.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Places/get_places_id

    Example:
        >>> response = get_places_by_id([67591, 89191])
        >>> print(format_places(response))
        [89191] Conservation Area Riversdale
        [67591] Riversdale Beach

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_places_by_id.py

    Args:
        place_id: Get a place with this ID. Multiple values are allowed.

    Returns:
        Response dict containing place records
    """
    r = node_api_get('places', ids=place_id, user_agent=user_agent)
    r.raise_for_status()

    # Convert coordinates to floats
    response = r.json()
    response['results'] = convert_all_coordinates(response['results'])
    return response


@document_request_params([docs._bounding_box, docs._name])
def get_places_nearby(**params) -> JsonResponse:
    """
    Given an bounding box, and an optional name query, return places nearby

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Places/get_places_nearby

    Example:
        >>> bounding_box = (150.0, -50.0, -149.999, -49.999)
        >>> response = get_places_nearby(*bounding_box)

        Response is split into standard (curated) places and community (non-curated) places:

        >>> print(len(response['results']['standard']))
        10
        >>> print(len(response['results']['community']))
        10

        Show basic info for all places in response:

        >>> print(format_places(response, align=True))
        Standard:
        [   97394] North America
        [   97395] Asia
        [   97393] Oceania
        ...
        Community:
        [  166719] Burgenland (accurate border)
        [   11770] Mehedinti
        [  119755] Mahurangi College
        ...

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_places_nearby.py

    Returns:
        Response dict containing place records, divided into 'standard' and 'community' places.
    """
    r = node_api_get('places/nearby', params=params)
    r.raise_for_status()
    return convert_all_place_coordinates(r.json())


@document_request_params([docs._search_query, docs._pagination])
@add_paginate_all(method='autocomplete')
def get_places_autocomplete(q: str = None, **params) -> JsonResponse:
    """Given a query string, get places with names starting with the search term

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Places/get_places_autocomplete

    **Note:** This endpoint accepts a ``per_page`` param, up to a max of 20 (default 10). Pages
    beyond the first page cannot be retrieved. Use ``page=all`` to attempt to retrieve additional
    results. See :py:func:`.paginate_autocomplete` for more info.

    Example:
        >>> response = get_places_autocomplete('Irkutsk')
        >>> print(format_places(response))
        [   11803] Irkutsk
        [   41854] Irkutskiy rayon
        [  166186] Irkutsk Oblast - ADD
        [  163077] Irkutsk agglomeration

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_places_autocomplete.py

    Args:
        q: Name must begin with this value

    Returns:
        Response dict containing place records
    """
    r = node_api_get('places/autocomplete', params={'q': q, **params})
    r.raise_for_status()

    # Convert coordinates to floats
    response = r.json()
    response['results'] = convert_all_coordinates(response['results'])
    return response


# Projects
# --------------------


@document_request_params([docs._projects_params, docs._pagination])
@add_paginate_all(method='page')
def get_projects(**params) -> JsonResponse:
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

        >>> print(format_projects(response, align=True))
        [    8291] PNW Invasive Plant EDDR
        [   19200] King County (WA) Noxious and Invasive Weeds
        [  102925] Keechelus/Kachess Invasive Plants
        ...


        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_projects.py

    Returns:
        Response dict containing project records
    """
    validate_multiple_choice_param(params, 'order_by', PROJECT_ORDER_BY_PROPERTIES)
    r = node_api_get('projects', params=params)
    r.raise_for_status()

    response = r.json()
    response['results'] = convert_all_coordinates(response['results'])
    response['results'] = convert_all_timestamps(response['results'])
    return response


def get_projects_by_id(
    project_id: MultiInt, rule_details: bool = None, user_agent: str = None
) -> JsonResponse:
    """Get one or more projects by ID.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Projects/get_projects_id

    Example:

        >>> response = get_projects_by_id([8348, 6432])
        >>> print(format_projects(response))
        [8348] Tucson High Native and Invasive Species Inventory
        [6432] CBWN Invasive Plants

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_projects_by_id.py

    Args:
        project_id: Get projects with this ID. Multiple values are allowed.
        rule_details: Return more information about project rules, for example return a full taxon
            object instead of simply an ID

    Returns:
        Response dict containing project records
    """
    r = node_api_get(
        'projects',
        ids=project_id,
        params={'rule_details': rule_details},
        user_agent=user_agent,
    )
    r.raise_for_status()

    response = r.json()
    response['results'] = convert_all_coordinates(response['results'])
    response['results'] = convert_all_timestamps(response['results'])
    return response


# Taxa
# --------------------


@document_request_params([docs._taxon_params, docs._taxon_id_params, docs._pagination])
@add_paginate_all(method='page')
def get_taxa(**params) -> JsonResponse:
    """Given zero to many of following parameters, get taxa matching the search criteria.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa

    Example:

        >>> response = get_taxa(q='vespi', rank=['genus', 'family'])
        >>> print(format_taxa(response))
        [52747] Family: Vespidae (Hornets, Paper Wasps, Potter Wasps, and Allies)
        [92786] Genus: Vespicula
        [646195] Genus: Vespiodes
        ...

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_taxa.json
                :language: JSON

    Returns:
        Response dict containing taxon records
    """
    params = translate_rank_range(params)
    r = node_api_get('taxa', params=params)
    r.raise_for_status()

    taxa = r.json()
    taxa['results'] = convert_all_timestamps(taxa['results'])
    return taxa


def get_taxa_by_id(taxon_id: MultiInt, user_agent: str = None) -> JsonResponse:
    """Get one or more taxa by ID.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa_id

    Example:

        >>> response = get_taxa_by_id(343248)
        >>> basic_fields = ['preferred_common_name', 'observations_count', 'wikipedia_url', 'wikipedia_summary']
        >>> print({f: response['results'][0][f] for f in basic_fields})
        {
            'preferred_common_name': 'Paper Wasps',
            'observations_count': 69728,
            'wikipedia_url': 'http://en.wikipedia.org/wiki/Polistinae',
            'wikipedia_summary': 'The Polistinae are eusocial wasps closely related to yellow jackets...',
        }

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_taxa_by_id.py

    Args:
        taxon_id: Get taxa with this ID. Multiple values are allowed.

    Returns:
        Response dict containing taxon records
    """
    r = node_api_get('taxa', ids=taxon_id, user_agent=user_agent)
    r.raise_for_status()

    taxa = r.json()
    taxa['results'] = convert_all_timestamps(taxa['results'])
    return taxa


@document_request_params([docs._taxon_params])
def get_taxa_autocomplete(**params) -> JsonResponse:
    """Given a query string, return taxa with names starting with the search term

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa_autocomplete

    **Note:** There appears to currently be a bug in the API that causes ``per_page`` to not have
    any effect.

    Example:

        Get just the name of the first matching taxon:

        >>> response = get_taxa_autocomplete(q='vespi')
        >>> print(response['results'][0]['name'])
        'Vespidae'

        Get basic info for taxa in response:

        >>> print(format_taxa(response, align=True))
        [   52747]       Family: Vespidae (Hornets, Paper Wasps, Potter Wasps, and Allies)
        [   84738]    Subfamily: Vespinae (Hornets and Yellowjackets)
        [  131878]      Species: Nicrophorus vespillo (Vespillo Burying Beetle)

        If you get unexpected matches, the search likely matched a synonym, either in the form of a
        common name or an alternative classification. Check the ``matched_term`` property for more
        info. For example:

        >>> first_result = get_taxa_autocomplete(q='zygoca')['results'][0]
        >>> first_result["name"]
        "Schlumbergera truncata"  # This doesn't look like our search term!
        >>> first_result["matched_term"]
        "Zygocactus truncatus"    # ...Because it matched an older synonym for Schlumbergera

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_taxa_autocomplete.py

        .. admonition:: Example Response (formatted)
            :class: toggle

            .. literalinclude:: ../sample_data/get_taxa_autocomplete_minified.py

    Returns:
        Response dict containing taxon records
    """
    params = translate_rank_range(params)
    r = node_api_get('taxa/autocomplete', params=params)
    r.raise_for_status()
    return r.json()


# Users
# --------------------


def get_user_by_id(user_id: int, user_agent: str = None) -> JsonResponse:
    """Get a user by ID.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Users/get_users_id

    Args:
        user_id: Get the user with this ID. Only a single ID is allowed per request.

    Example:

        >>> response = get_user_by_id(123456)
        >>> print(format_users(response))
        [1234] my_username

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_user_by_id.py

    Returns:
        Response dict containing user record
    """
    r = node_api_get('users', ids=[user_id], user_agent=user_agent)
    r.raise_for_status()
    results = r.json()['results']
    if not results:
        return {}
    return convert_generic_timestamps(results[0])


@document_request_params([docs._search_query, docs._project_id, docs._pagination])
def get_users_autocomplete(q: str, **params) -> JsonResponse:
    """Given a query string, return users with names or logins starting with the search term

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Users/get_users_autocomplete

    Note: Pagination is supported; default page size is 6, and max is 100.

    Example:

        >>> response = get_taxa_autocomplete(q='my_userna')
        >>> print(format_users(response))
        [1234] my_username
        [12345] my_username_2

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_users_autocomplete.py

    Returns:
        Response dict containing user records
    """
    r = node_api_get('users/autocomplete', params={'q': q, **params})
    r.raise_for_status()
    users = r.json()
    users['results'] = convert_all_timestamps(users['results'])
    return users
