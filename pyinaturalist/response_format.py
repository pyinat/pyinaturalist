""" Helper functions for formatting API responses """
# TODO: Should most formatting/converting be handled by attrs converters?
from datetime import datetime, timedelta
from dateutil.parser import parse as parse_date
from dateutil.parser._parser import UnknownTimezoneWarning
from dateutil.tz import tzoffset
from logging import getLogger
from typing import Any, Dict, Iterable, List, Optional, Union
from warnings import catch_warnings, simplefilter

from pyinaturalist.constants import (
    Coordinates,
    Dimensions,
    HistogramResponse,
    JsonResponse,
    ResponseObject,
)

GENERIC_TIME_FIELDS = ('created_at', 'last_post_at', 'updated_at')
OBSERVATION_TIME_FIELDS = (
    'created_at_details',
    'created_time_zone',
    'observed_on',
    'observed_on_details',
    'observed_on_string',
    'observed_time_zone',
    'time_zone_offset',
)
logger = getLogger(__name__)


# GeoJSON conversion
# --------------------


def as_geojson_feature_collection(
    results: Iterable[ResponseObject], properties: List[str] = None
) -> Dict[str, Any]:
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


def as_geojson_feature(result: ResponseObject, properties: List[str] = None) -> ResponseObject:
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


# Wrapper functions to apply conversions to all response objects
# --------------------


def convert_all_coordinates(results: List[ResponseObject]) -> List[ResponseObject]:
    """Convert coordinate pairs in response items from strings to floats, if valid

    Args:
        results: Results from API response; expects coordinates in either 'location' key or
            'latitude' and 'longitude' keys
    """
    results = [convert_lat_long_dict(result) for result in results]
    results = [convert_lat_long_list(result) for result in results]
    return results


def convert_all_place_coordinates(response: JsonResponse) -> JsonResponse:
    """Convert locations for both standard and community-contributed places to floats"""
    response['results'] = {
        'standard': convert_all_coordinates(response['results'].get('standard')),
        'community': convert_all_coordinates(response['results'].get('community')),
    }
    return response


def convert_all_timestamps(results: List[ResponseObject]) -> List[ResponseObject]:
    """Replace all date/time info with datetime objects, where possible"""
    results = [convert_generic_timestamps(result) for result in results]
    results = [convert_observation_timestamps(result) for result in results]
    return results


# Type conversion functions
# --------------------


def convert_lat_long(obj: Union[Dict, List, str]) -> Optional[Coordinates]:
    """Convert a coordinate pair as a dict, list, or string into a pair of floats, if valid"""
    if isinstance(obj, str):
        return try_float_pair(*str(obj).split(','))
    elif isinstance(obj, list):
        return try_float_pair(*obj)
    elif isinstance(obj, dict):
        return try_float_pair(obj.get('latitude'), obj.get('longitude'))


def convert_lat_long_dict(result: ResponseObject) -> ResponseObject:
    """Convert a coordinate pair dict within a response to floats, if valid"""
    if 'latitude' in result and 'longitude' in result:
        result['latitude'] = try_float(result['latitude'])
        result['longitude'] = try_float(result['longitude'])
    return result


def convert_lat_long_list(result: ResponseObject):
    """Convert a coordinate pairs in a response item from strings to floats, if valid"""
    # Format inner record if present, e.g. for search results
    if 'record' in result:
        result['record'] = convert_lat_long_list(result['record'])
        return result

    if ',' in (result.get('location') or ''):
        result['location'] = [try_float(coord) for coord in result['location'].split(',')]
    return result


def convert_generic_timestamps(result: ResponseObject) -> ResponseObject:
    """Replace generic created/updated info that's returned by multiple endpoints.
    **Note:** Compared to observation timestamps, these are generally more reliable. These seem to
    be consistently in ISO 8601 format.
    """
    # Format inner record if present, e.g. for search results
    if 'record' in result:
        result['record'] = convert_generic_timestamps(result['record'])
        return result

    for field in GENERIC_TIME_FIELDS:
        datetime_obj = try_datetime(result.get(field, ''))
        if datetime_obj:
            result[field] = datetime_obj
    return result


# TODO: pick either this or attrs version
def convert_observation_timestamps(result: ResponseObject) -> ResponseObject:
    """Replace observation date/time info with datetime objects"""
    if 'created_at_details' not in result and 'observed_on_string' not in result:
        return result

    observation = result.copy()
    tz_offset = observation.get('time_zone_offset', '')
    tz_name = observation.get('observed_time_zone')

    created_datetime = observation.get('created_at')
    if not isinstance(created_datetime, datetime):
        created_datetime = try_datetime(observation.get('created_at_details', {}).get('date'))
        created_datetime = convert_offset(created_datetime, tz_offset, tz_name)

    # Ignore any timezone info in observed_on timestamp; offset field is more reliable
    observed_datetime = try_datetime(observation.get('observed_on_string', ''), ignoretz=True)
    observed_datetime = convert_offset(observed_datetime, tz_offset, tz_name)

    # If valid, add the datetime objects and remove all other redundant date/time fields
    if created_datetime and observed_datetime:
        for field in OBSERVATION_TIME_FIELDS:
            observation.pop(field, None)
    observation['created_at'] = created_datetime
    observation['observed_on'] = observed_datetime

    return observation


def convert_observation_timestamp(
    timestamp: str, tz_offset: str = None, tz_name: str = None, ignoretz: bool = False
) -> Optional[datetime]:
    """Convert an observation timestamp + timezone info to a datetime. This is needed because
    observed_on and created_at can be in in inconsistent (user-submitted?) formats.
    """
    dt = try_datetime(timestamp, ignoretz=ignoretz)
    return convert_offset(dt, tz_offset, tz_name)


def convert_offset(
    datetime_obj: Optional[datetime], tz_offset: str = None, tz_name: str = None
) -> Optional[datetime]:
    """Use timezone offset info to replace a datetime's tzinfo"""
    if not datetime_obj or not tz_offset:
        return datetime_obj

    try:
        offset = parse_offset(tz_offset, tz_name)
        return datetime_obj.replace(tzinfo=offset)
    except (AttributeError, TypeError, ValueError) as e:
        logger.debug(f'Could not parse offset: {tz_offset}: {str(e)}')
        return None


def parse_offset(tz_offset: str, tz_name: str = None) -> tzoffset:
    """Convert a timezone offset string to a tzoffset object, accounting for some common variations
    in format

    Examples:

        >>> parse_offset('GMT-08:00', 'PST')
        tzoffset('PST', -28800)
        >>> parse_offset('-06:00')
        tzoffset(None, -21600)
        >>> parse_offset('+05:30')
        tzoffset(None, 19800)
        >>> parse_offset('0530')
        tzoffset(None, 19800)

    """

    def remove_prefixes(text, prefixes):
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix) :]  # noqa  # black and flake8 fight over this one
        return text

    # Parse hours, minutes, and sign from offset string; account for either `hh:mm` or `hhmm` format
    tz_offset = remove_prefixes(tz_offset, ['GMT', 'UTC']).strip()
    multiplier = -1 if tz_offset.startswith('-') else 1
    tz_offset = tz_offset.lstrip('+-')
    if ':' in tz_offset:
        hours, minutes = tz_offset.split(':')
    else:
        hours, minutes = tz_offset[:2], tz_offset[2:]

    # Convert to a timezone offset in +/- seconds
    delta = timedelta(hours=int(hours), minutes=int(minutes))
    return tzoffset(tz_name, delta.total_seconds() * multiplier)


def try_datetime(timestamp: Any, **kwargs) -> Optional[datetime]:
    """Parse a timestamp string into a datetime, if valid; return ``None`` otherwise"""
    if isinstance(timestamp, datetime):
        return timestamp
    if not timestamp or not str(timestamp).strip():
        return None

    try:
        # Suppress UnknownTimezoneWarning
        with catch_warnings():
            simplefilter('ignore', category=UnknownTimezoneWarning)
            return parse_date(timestamp, **kwargs)
    except (AttributeError, TypeError, ValueError) as e:
        logger.debug(f'Could not parse timestamp: {timestamp}: "{str(e)}"')
        return None


def try_float(value: Any) -> Optional[float]:
    """Convert a value to a float, if valid; return ``None`` otherwise"""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def try_float_pair(*values: Any) -> Optional[Coordinates]:
    """Convert a pair of coordinat values to floats, if both are valid; return ``None`` otherwise"""
    if len(values) != 2:
        return None
    try:
        return float(values[0]), float(values[1])
    except (TypeError, ValueError):
        return None


def try_int(value: Any) -> Optional[float]:
    """Convert a value to a int, if valid; return ``None`` otherwise"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def try_int_or_float(value: Any) -> Union[int, float, None]:
    """Convert a value to either an int or a float, if valid; return ``None`` otherwise"""
    return try_int(str(value)) or try_float(str(value))


# Formatting Functions
# --------------------


def format_dimensions(dimensions: Union[Dict[str, int], Dimensions]) -> Dimensions:
    """Slightly simplify 'dimensions' response attribute into ``(width, height)`` tuple"""
    if isinstance(dimensions, tuple):
        return dimensions
    return dimensions.get("width", 0), dimensions.get("height", 0)


# TODO: Will be used for Photo model
# def format_file_size(value) -> str:
#     """Convert a file size in bytes into a human-readable format"""
#     for unit in ['B', 'KiB', 'MiB', 'GiB']:
#         if abs(value) < 1024.0:
#             return f'{value:.2f}{unit}'
#         value /= 1024.0
#     return f'{value:.2f}TiB'


def format_license(value: str) -> str:
    return str(value).upper().replace('_', '-')


def flatten_nested_params(observation: ResponseObject) -> ResponseObject:
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


def format_histogram(response: JsonResponse) -> HistogramResponse:
    """Format a response containing time series data into a single ``{date: value}`` dict"""
    # The inner result object's key will be the name of the interval requested
    interval = next(iter(response['results'].keys()))
    histogram = response['results'][interval]

    # Convert keys to appropriate type depending on interval
    if interval in ['month_of_year', 'week_of_year']:
        return {int(k): v for k, v in histogram.items()}
    else:
        return {parse_date(k): v for k, v in histogram.items()}


def safe_split(value: str = None, delimiter: str = '|') -> List[str]:
    if not value:
        return []
    return str(value).split(delimiter)
