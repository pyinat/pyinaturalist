""" Helper functions for formatting API responses """
from datetime import datetime, timedelta
from dateutil.parser import parse as parse_date
from dateutil.parser._parser import UnknownTimezoneWarning
from dateutil.tz import tzoffset
from logging import getLogger
from typing import Any, Dict, Iterable, List, Optional
from warnings import catch_warnings, simplefilter

logger = getLogger(__name__)


def as_geojson_feature_collection(
    results: Iterable[Dict[str, Any]], properties: List[str] = None
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
    return {
        "type": "FeatureCollection",
        "features": [as_geojson_feature(record, properties) for record in results],
    }


def as_geojson_feature(result: Dict[str, Any], properties: List[str] = None) -> Dict[str, Any]:
    """
    Convert an individual response item to a geojson Feature object, optionally with specific
    response properties included.

    Args:
        result: A single response item
        properties: Whitelist of specific properties to include
    """
    result["geojson"]["coordinates"] = [float(i) for i in result["geojson"]["coordinates"]]
    return {
        "type": "Feature",
        "geometry": result["geojson"],
        "properties": {k: result.get(k) for k in properties or []},
    }


def convert_float(value: Any) -> Optional[float]:
    """ Convert a value to a float, if valid; return ``None`` otherwise """
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def convert_lat_long_to_float(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert coordinate pairs in response items from strings to floats, if valid

    Args:
        results: Results from API response; expects coordinates in "latitude" and "longitude" keys
    """
    for result in results:
        result["latitude"] = convert_float(result["latitude"])
        result["longitude"] = convert_float(result["longitude"])
    return results


def convert_location_to_float(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert coordinate pairs in response items from strings to floats, if valid.

    Args:
        results: Results from API response; expects coordinates in the "location" key
    """
    for result in results or []:
        if "," in (result["location"] or ""):
            result["location"] = [convert_float(coord) for coord in result["location"].split(",")]
    return results


def flatten_nested_params(observation: Dict[str, Any]) -> Dict[str, Any]:
    """Extract some nested observation properties to include at the top level;
     this makes it easier to specify these as properties for
     :py:func:`.as_as_geojson_feature_collection`.

    Args:
        observation: A single observation result
    """
    taxon = observation.get("taxon", {})
    photos = observation.get("photos", [{}])
    observation["taxon_id"] = taxon.get("id")
    observation["taxon_name"] = taxon.get("name")
    observation["taxon_rank"] = taxon.get("rank")
    observation["taxon_common_name"] = taxon.get("preferred_common_name")
    observation["photo_url"] = photos[0].get("url")
    return observation


def format_observation(observation: Dict) -> str:
    """Make a condensed summary from basic observation details: what, who, when, where"""
    taxon_str = format_taxon(observation.get("taxon") or {})
    location = observation.get("place_guess") or observation.get("location")
    return (
        f'[{observation["id"]}] {taxon_str} '
        f'observed by {observation["user"]["login"]} '
        f'on {observation["observed_on"]} '
        f"at {location}"
    )


def format_taxon(taxon: Dict, align: bool = False) -> str:
    """Format a taxon result into a single string containing taxon ID, rank, and name
    (including common name, if available).
    """
    if not taxon:
        return "unknown taxon"
    common_name = taxon.get("preferred_common_name")
    name = f'{taxon["name"]}' + (f" ({common_name})" if common_name else "")
    rank = taxon["rank"].title()

    # Visually align taxon IDs (< 7 chars) and ranks (< 11 chars)
    if align:
        # return "{:>8}: {:>12} {}".format(taxon["id"], rank, name)
        return f'{taxon["id"]:>8}: {rank:>12} {name}'
    else:
        return f"{rank}: {name})"


def parse_observation_timestamp(observation: Dict) -> Optional[datetime]:
    """Parse a timestamp string, accounting for variations in timezone information"""
    # Attempt a straightforward parse from any dateutil-supported format
    # Ignore timezone in timestamp; offset field is more reliable
    timestamp = observation["observed_on_string"]
    observed_on = _try_parse_date(timestamp, ignoretz=True)
    if not observed_on:
        return None

    # Attempt to get timezone info from separate offset field
    try:
        offset = parse_offset(observation["time_zone_offset"])
        return observed_on.replace(tzinfo=offset)
    except (AttributeError, TypeError) as e:
        logger.warning(f'Could not parse offset: {observation["time_zone_offset"]}: {str(e)}')
        return None


def parse_offset(offset_str: str) -> tzoffset:
    """Convert a timezone offset string to a tzoffset object, accounting for some common variations
    in format

    Examples:

        >>> parse_offset('GMT-08:00')
        tzoffset(None, -28800)
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
    offset_str = remove_prefixes(offset_str, ["GMT", "UTC"]).strip()
    multiplier = -1 if offset_str.startswith("-") else 1
    offset_str = offset_str.lstrip("+-")
    if ":" in offset_str:
        hours, minutes = offset_str.split(":")
    else:
        hours, minutes = offset_str[:2], offset_str[2:]

    # Convert to a timezone offset in +/- seconds
    delta = timedelta(hours=int(hours), minutes=int(minutes))
    return tzoffset(None, delta.total_seconds() * multiplier)


def _try_parse_date(timestamp: str, **kwargs) -> Optional[datetime]:
    try:
        # Suppress UnknownTimezoneWarning
        with catch_warnings():
            simplefilter("ignore", category=UnknownTimezoneWarning)
            return parse_date(timestamp, **kwargs)
    except (AttributeError, TypeError) as e:
        logger.warning(f"Could not parse timestamp: {timestamp}: {str(e)}")
        return None
