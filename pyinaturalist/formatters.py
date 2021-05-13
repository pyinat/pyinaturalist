"""Extra functions to help preview response content, not used directly by API functions.

These functions will accept any of the following:

* A JSON response
* A list of response objects
* A single response object
"""
from copy import deepcopy
from logging import getLogger
from typing import List, Sequence

from pyinaturalist.constants import ResponseObject, ResponseOrObject

__all__ = ['format_observations', 'format_species_counts', 'format_taxa', 'simplify_observations']
logger = getLogger(__name__)


def format_observations(observations: ResponseOrObject, align: bool = False) -> str:
    """Format observation results into a condensed summary: id, what, who, when, and where"""
    obs_strings = [_format_observation(o, align=align) for o in _ensure_list(observations)]
    return '\n'.join(obs_strings)


def _format_observation(observation: ResponseObject, align: bool = False) -> str:
    taxon_str = _format_taxon(observation.get('taxon') or {}, align=align)
    location = observation.get('place_guess') or observation.get('location')
    if align:
        return (
            f"[{observation['id']:>8}] {taxon_str}"
            f"\n    observed by {observation['user']['login']} "
            f"on {observation['observed_on']} at {location}"
        )
    else:
        return (
            f"[{observation['id']}] {taxon_str} "
            f"observed by {observation['user']['login']} "
            f"on {observation['observed_on']} at {location}"
        )


def format_species_counts(species_counts: ResponseOrObject, align: bool = False) -> str:
    """Format observation species counts"""
    count_strings = [_format_species_count(t, align=align) for t in _ensure_list(species_counts)]
    return '\n'.join(count_strings)


def _format_species_count(species_count: ResponseObject, align: bool = False) -> str:
    taxon = _format_taxon(species_count['taxon'], align=align)
    return f'{taxon}: {species_count["count"]}'


def format_taxa(taxa: ResponseOrObject, align: bool = False) -> str:
    """Format taxon results into a single string containing taxon ID, rank, and name
    (including common name, if available).
    """
    taxon_strings = [_format_taxon(t, align=align) for t in _ensure_list(taxa)]
    return '\n'.join(taxon_strings)


def _format_taxon(taxon: ResponseObject, align: bool = False) -> str:
    if not taxon:
        return 'unknown taxon'
    common_name = taxon.get('preferred_common_name')
    name = f"{taxon['name']}" + (f' ({common_name})' if common_name else '')
    rank = taxon['rank'].title()

    # Visually align taxon IDs (< 7 chars) and ranks (< 11 chars)
    if align:
        return f"[{taxon['id']:>8}] {rank:>12} {name:>55}"
    else:
        return f"[{taxon['id']}] {rank}: {name}"


def simplify_observations(
    observations: ResponseOrObject, align: bool = False
) -> List[ResponseObject]:
    """Flatten out some nested data structures within observation recorda:

    * annotations
    * comments
    * identifications
    * non-owner IDs
    """
    return [_simplify_observation(o) for o in _ensure_list(observations)]


def _simplify_observation(obs):
    # Reduce annotations to IDs and values
    obs = deepcopy(obs)
    obs['annotations'] = [
        (a['controlled_attribute_id'], a['controlled_value_id']) for a in obs['annotations']
    ]

    # Reduce identifications to just a list of identification IDs and taxon IDs
    obs['identifications'] = [(i['id'], i['taxon_id']) for i in obs['identifications']]
    obs['non_owner_ids'] = [(i['id'], i['taxon_id']) for i in obs['non_owner_ids']]

    # Reduce comments to usernames and comment text
    obs['comments'] = [(c['user']['login'], c['body']) for c in obs['comments']]
    del obs['observation_photos']

    return obs


def _ensure_list(obj: ResponseOrObject) -> List:
    if isinstance(obj, dict) and 'results' in obj:
        return obj['results']
    elif isinstance(obj, Sequence):
        return list(obj)
    else:
        return [obj]
