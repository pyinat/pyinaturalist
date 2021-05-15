"""Extra functions to help preview response content, not used directly by API functions.

These functions will accept any of the following:

* A JSON response
* A list of response objects
* A single response object

They will also accept the option ``align=True`` to align values where possible.
"""
# TODO: Use tabulate library for aligning values?
from copy import deepcopy
from logging import getLogger
from typing import Any, Callable, List, Sequence

from pyinaturalist.constants import ResponseObject, ResponseOrObject

__all__ = [
    'format_controlled_terms',
    'format_identifications',
    'format_observations',
    'format_places',
    'format_projects',
    'format_search_results',
    'format_species_counts',
    'format_taxa',
    'format_users',
    'simplify_observations',
]
logger = getLogger(__name__)


def format_controlled_terms(terms: ResponseOrObject, align: bool = False) -> str:
    """Format controlled term results into a condensed list of terms and values"""
    return _format_objects(terms, align, _format_controlled_term)


def _format_controlled_term(term: ResponseObject, **kwargs) -> str:
    term_values = [f'    {value["id"]}: {value["label"]}' for value in term['values']]
    return f'{term["id"]}: {term["label"]}\n' + '\n'.join(term_values)


def format_identifications(identifications: ResponseOrObject, align: bool = False) -> str:
    """Format identification results into a condensed summary: id, what, when, and who"""
    return _format_objects(identifications, align, _format_identification)


def _format_identification(ident: ResponseObject, align: bool = False) -> str:
    ident_id = pad(ident['id'], 8, align)
    taxon = _format_taxon(ident['taxon'], align=align)
    category = pad(ident['category'], 10, align)
    return f"[{ident_id}] {taxon} ({category}) added on {ident['created_at']} by {ident['user']['login']}"


def format_observations(observations: ResponseOrObject, align: bool = False) -> str:
    """Format observation results into a condensed summary: id, what, when, who, and where"""
    return _format_objects(observations, align, _format_observation)


def _format_observation(obs: ResponseObject, align: bool = False) -> str:
    taxon_str = _format_taxon(obs.get('taxon') or {}, align=align)
    location = obs.get('place_guess') or obs.get('location')
    obs_id = f"{obs['id']:>8}" if align else f"{obs['id']}"
    separator = '\n    ' if align else ' '

    return (
        f"[{obs_id}] {taxon_str}{separator}"
        f"observed on {obs['observed_on']} by {obs['user']['login']} at {location}"
    )


def format_places(places: ResponseOrObject, align: bool = False) -> str:
    """Format place results into a condensed list of IDs and names"""
    return _format_objects(places, align, _format_place)


def _format_place(place: ResponseObject, align: bool = False) -> str:
    if 'standard' in place and 'community' in place:
        standard_places = format_places(place['standard'], align)
        community_places = format_places(place['community'], align)
        return f'Standard:\n{standard_places}\n\nCommunity:\n{community_places}'

    place_id = pad(place['id'], 8, align)
    return f"[{place_id}] {place['name']}"


def format_projects(projects: ResponseOrObject, align: bool = False) -> str:
    """Format project results into a condensed list of IDs and titles"""
    return _format_objects(projects, align, _format_project)


def _format_project(project: ResponseObject, align: bool = False) -> str:
    project_id = pad(project['id'], 8, align)
    return f"[{project_id}] {project['title']}"


def format_search_results(search_results: ResponseOrObject, align: bool = False) -> str:
    """Format search results into a condensed list of values depending on result type"""
    return _format_objects(search_results, align, _format_search_result)


def _format_search_result(result: ResponseObject, align: bool = False) -> str:
    """Format a search result depending on its type"""
    search_formatters = {
        'Place': _format_place,
        'Project': _format_project,
        'Taxon': _format_taxon,
        'User': _format_user,
    }
    formatter = search_formatters[result['type']]
    record_str = formatter(result['record'], align)
    type_str = pad(result['type'], 7, align)
    return f'[{type_str}] {record_str}'


def format_species_counts(species_counts: ResponseOrObject, align: bool = False) -> str:
    """Format observation species counts into a condensed list of names and # of observations"""
    return _format_objects(species_counts, align, _format_species_count)


def _format_species_count(species_count: ResponseObject, align: bool = False) -> str:
    taxon = _format_taxon(species_count['taxon'], align=align)
    return f'{taxon}: {species_count["count"]}'


def format_taxa(taxa: ResponseOrObject, align: bool = False) -> str:
    """Format taxon results into a single string containing taxon ID, rank, and name
    (including common name, if available).
    """
    return _format_objects(taxa, align, _format_taxon)


def _format_taxon(taxon: ResponseObject, align: bool = False) -> str:
    if not taxon:
        return 'unknown taxon'
    if 'name' not in taxon:
        return _format_taxon_rank_id(taxon, align=align)

    taxon_id = pad(taxon["id"], 8, align)
    rank = pad(taxon['rank'].title(), 12, align)
    common_name = taxon.get('preferred_common_name')
    name = f"{taxon['name']}" + (f' ({common_name})' if common_name else '')

    return f'[{taxon_id}] {rank}: {name}'


def _format_taxon_rank_id(taxon: ResponseObject, align: bool = False) -> str:
    """Format a taxon that only has a rank and ID"""
    rank = pad(taxon['rank'].title(), 12, align)
    taxon_id = pad(taxon['id'], 8, align)
    return f'{rank}: {taxon_id}'


def format_users(users: ResponseOrObject, align: bool = False) -> str:
    """Format user results into a condensed list of IDs, usernames, and real names"""
    return _format_objects(users, align, _format_user)


def _format_user(user: ResponseObject, align: bool = False) -> str:
    # Response object may contain a nested 'user' object
    if 'user' in user:
        user = user['user']

    user_id = pad(user['id'], 8, align)
    real_name = f" ({user['name']})" if user.get('name') else ''
    return f"[{user_id}] {user['login']}{real_name}"


def simplify_observations(
    observations: ResponseOrObject, align: bool = False
) -> List[ResponseObject]:
    """Flatten out some nested data structures within observation records:

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
        obj = obj['results']
    if isinstance(obj, Sequence):
        return list(obj)
    else:
        return [obj]


def _format_objects(obj: ResponseOrObject, align: bool, format_func: Callable):
    """Generic function to format a response, object, or list of objects"""
    obj_strings = [format_func(t, align=align) for t in _ensure_list(obj)]
    return '\n'.join(obj_strings)


def pad(value: Any, width: int, align: bool):
    return str(value).rjust(width) if align else value
