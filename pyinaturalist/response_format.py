""" Helper functions for formatting API responses """
from typing import Any, Dict, List, Iterable

from pyinaturalist.constants import RANKS


def as_geojson_feature_collection(
    results: Iterable[Dict[str, Any]], properties: List[str] = None
) -> Dict[str, Any]:
    """"
    Convert results from an API response into a
    `geojson FeatureCollection<https://tools.ietf.org/html/rfc7946#section-3.3>`_ object.
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
    """"
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
    """ Extract some nested observation properties to include at the top level;
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
        taxon["id"], taxon["rank"].title(), taxon["name"], " ({})".format(common) if common else "",
    )


def _get_rank_range(min_rank: str = None, max_rank: str = None) -> List[str]:
    """ Translate min and/or max rank into a list of ranks """
    min_rank_index = _get_rank_index(min_rank) if min_rank else 0
    max_rank_index = _get_rank_index(max_rank) + 1 if max_rank else len(RANKS)
    return RANKS[min_rank_index:max_rank_index]


def _get_rank_index(rank: str) -> int:
    if rank not in RANKS:
        raise ValueError("Invalid rank")
    return RANKS.index(rank)
