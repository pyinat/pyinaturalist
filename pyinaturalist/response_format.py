""" Helper functions for formatting API responses """
from typing import Any, Dict, List, Iterable, Optional


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
    observation["preferred_common_name"] = taxon.get("preferred_common_name")
    observation["photo_url"] = photos[0].get("url")
    return observation


def format_taxon(taxon: Dict) -> str:
    """Format a taxon result into a single string containing taxon ID, rank, and name
    (including common name, if available).
    """
    # Visually align taxon IDs (< 7 chars) and ranks (< 11 chars)
    common = taxon.get("preferred_common_name")
    return "{:>8}: {:>12} {}{}".format(
        taxon["id"],
        taxon["rank"].title(),
        taxon["name"],
        " ({})".format(common) if common else "",
    )


def convert_location_to_float(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert coordinate pairs in response items from strings to floats, if valid.

    Args:
        results: Results from API response; expects coordinates in the "location" key
    """
    for result in results or []:
        if "," in (result["location"] or ""):
            result["location"] = [convert_float(coord) for coord in result["location"].split(",")]
    return results


def convert_lat_long_to_float(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert coordinate pairs in response items from strings to floats, if valid

    Args:
        results: Results from API response; expects coordinates in "latitude" and "longitude" keys
    """
    for result in results:
        result["latitude"] = convert_float(result["latitude"])
        result["longitude"] = convert_float(result["longitude"])
    return results


def convert_float(value: Any) -> Optional[float]:
    """ Convert a value to a float, if valid; return ``None`` otherwise """
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
