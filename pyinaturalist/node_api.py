"""Placeholder module for backwards-compatibility"""
# flake8: noqa: F401, F403
from typing import Iterable, List
from warnings import warn

from pyinaturalist.constants import JsonResponse, ResponseResult
from pyinaturalist.pagination import paginate_all
from pyinaturalist.v1 import *
from pyinaturalist.v1 import get_observations

msg = (
    'The module `pyinaturalist.node_api` is deprecated; please use `from pyinaturalist import ...`'
)
warn(DeprecationWarning(msg))


def get_all_observations(**params) -> List[JsonResponse]:
    """Deprecated; use ``get_observations(page='all')`` instead"""
    msg = "get_all_observations() is deprecated; please use get_observations(page='all') instead"
    warn(DeprecationWarning(msg))
    return paginate_all(get_observations, method='id', **params)['results']


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
    warn(DeprecationWarning('get_geojson_observations() has been moved to pyinaturalist-convert'))
    params['mappable'] = True
    params['page'] = 'all'
    response = get_observations(**params)
    return as_geojson_feature_collection(
        response['results'],
        properties=properties if properties is not None else DEFAULT_OBSERVATION_ATTRS,
    )


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


def as_geojson_feature_collection(
    results: Iterable[ResponseResult], properties: List[str] = None
) -> JsonResponse:
    """
    Convert results from an API response into a
    `geojson FeatureCollection <https://tools.ietf.org/html/rfc7946#section-3.3>`_ object.
    This is currently only used for observations, but could be used for any other responses with
    geospatial info.

    Args:
        results: List of results from API response
        properties: Whitelist of specific properties to include
    """
    results = [flatten_nested_params(obs) for obs in results]
    return {
        'type': 'FeatureCollection',
        'features': [as_geojson_feature(record, properties) for record in results],
    }


def as_geojson_feature(result: ResponseResult, properties: List[str] = None) -> ResponseResult:
    """
    Convert an individual response item to a geojson Feature object, optionally with specific
    response properties included.

    Args:
        result: A single response item
        properties: Whitelist of specific properties to include
    """
    result['geojson']['coordinates'] = [float(i) for i in result['geojson']['coordinates']]
    return {
        'type': 'Feature',
        'geometry': result['geojson'],
        'properties': {k: result.get(k) for k in properties or []},
    }


def flatten_nested_params(observation: ResponseResult) -> ResponseResult:
    """Extract some nested observation properties to include at the top level;
     this makes it easier to specify these as properties for
     :py:func:`.as_as_geojson_feature_collection`.

    Args:
        observation: A single observation result
    """
    taxon = observation.get('taxon', {})
    photos = observation.get('photos', [{}])
    observation['taxon_id'] = taxon.get('id')
    observation['taxon_name'] = taxon.get('name')
    observation['taxon_rank'] = taxon.get('rank')
    observation['taxon_common_name'] = taxon.get('preferred_common_name')
    observation['photo_url'] = photos[0].get('url')
    return observation
