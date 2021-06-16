"""Extra functions to help preview response content, not used directly by API functions.

These functions will accept any of the following:

* A JSON response
* A list of response objects
* A single response object

They will also accept the option ``align=True`` to align values where possible.
"""
from copy import deepcopy
from functools import partial
from logging import getLogger
from typing import Any, Callable, List, Sequence, Type

from pyinaturalist.constants import ResponseObject, ResponseOrObject
from pyinaturalist.models import (
    BaseModel,
    Identification,
    Observation,
    Place,
    Project,
    SearchResult,
    Taxon,
    User,
)

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


def format_species_counts(species_counts: ResponseOrObject, align: bool = False) -> str:
    """Format observation species counts into a condensed list of names and # of observations"""
    return _format_objects(species_counts, align, _format_species_count)


def _format_species_count(species_count: ResponseObject, align: bool = False) -> str:
    taxon = format_taxa(species_count['taxon'])
    return f'{taxon}: {species_count["count"]}'


def simplify_observations(observations: ResponseOrObject, align: bool = False) -> List[ResponseObject]:
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


def _format_model_objects(results: Any, cls: Type[BaseModel], **kwargs):
    """Generic function to format a response, object, or list of objects"""
    objects = cls.from_json_list(results)
    return '\n'.join([str(obj) for obj in objects])


# TODO: Figure out type annotations for these
format_identifications = partial(_format_model_objects, cls=Identification)
format_observations = partial(_format_model_objects, cls=Observation)
format_places = partial(_format_model_objects, cls=Place)
format_projects = partial(_format_model_objects, cls=Project)
format_search_results = partial(_format_model_objects, cls=SearchResult)
format_taxa = partial(_format_model_objects, cls=Taxon)
format_users = partial(_format_model_objects, cls=User)


def pad(value: Any, width: int, align: bool, right: bool = False):
    if not align:
        return value
    return str(value).rjust(width) if right else str(value).ljust(width)
