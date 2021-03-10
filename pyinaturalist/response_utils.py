"""Some utility functions that can simplify working with response data, but are not directly used in
any API functions.
"""
from copy import deepcopy

from pyinaturalist.constants import ResponseObject


def format_observation_str(observation: ResponseObject) -> str:
    """Make a condensed summary from basic observation details: what, who, when, where"""
    taxon_str = format_taxon_str(observation.get('taxon') or {})
    location = observation.get('place_guess') or observation.get('location')
    return (
        f"[{observation['id']}] {taxon_str} "
        f"observed by {observation['user']['login']} "
        f"on {observation['observed_on']} "
        f'at {location}'
    )


def format_taxon_str(taxon: ResponseObject, align: bool = False) -> str:
    """Format a taxon result into a single string containing taxon ID, rank, and name
    (including common name, if available).
    """
    if not taxon:
        return 'unknown taxon'
    common_name = taxon.get('preferred_common_name')
    name = f"{taxon['name']}" + (f' ({common_name})' if common_name else '')
    rank = taxon['rank'].title()

    # Visually align taxon IDs (< 7 chars) and ranks (< 11 chars)
    if align:
        return f"{taxon['id']:>8}: {rank:>12} {name}"
    else:
        return f'{rank}: {name}'


def simplify_observation(obs):
    """Simplify some nested data structures in an observation record"""
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


def to_dataframe(observations):
    """Normalize observation JSON into a DataFrame"""
    import pandas as pd

    return pd.json_normalize([simplify_observation(obs) for obs in observations])
