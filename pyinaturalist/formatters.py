"""Utilities for formatting API responses and model objects, for convenience/readability when exploring data.
Not used directly by API functions.

These functions will accept any of the following:

* A JSON response
* A list of response objects
* A single response object
"""
from copy import deepcopy
from datetime import date, datetime
from functools import partial
from logging import getLogger
from typing import Callable, List, Type

from pyinaturalist.constants import ResponseOrResults, ResponseResult
from pyinaturalist.converters import ensure_list
from pyinaturalist.models import (
    BaseModel,
    Identification,
    ModelObjects,
    Observation,
    Place,
    Project,
    SearchResult,
    Taxon,
    User,
)

# Use rich for pretty-printing, if installed
try:
    from rich import print
except ImportError:
    pass

logger = getLogger(__name__)


# TODO: A detect_type() function that also allows this to be used for response JSON?
def pprint(objects: ModelObjects):
    objects = _ensure_list(objects)
    cls = objects[0].__class__
    print(cls.to_table(objects))


def format_controlled_terms(terms: ResponseOrResults, **kwargs) -> str:
    """Format controlled term results into a condensed list of terms and values"""
    return _format_results(terms, _format_controlled_term)


def _format_controlled_term(term: ResponseResult, **kwargs) -> str:
    term_values = [f'    {value["id"]}: {value["label"]}' for value in term['values']]
    return f'{term["id"]}: {term["label"]}\n' + '\n'.join(term_values)


def format_species_counts(species_counts: ResponseOrResults, **kwargs) -> str:
    """Format observation species counts into a condensed list of names and # of observations"""
    return _format_results(species_counts, _format_species_count)


def _format_species_count(species_count: ResponseResult, **kwargs) -> str:
    taxon = format_taxa(species_count['taxon'])
    return f'{taxon}: {species_count["count"]}'


# TODO: Replace remaining functions that use this with _format_model_objects (requires more model changes)
def _format_results(obj: ResponseOrResults, format_func: Callable):
    """Generic function to format a response, result, or list of results"""
    obj_strings = [format_func(t) for t in ensure_list(obj)]
    return '\n'.join(obj_strings)


# TODO: This maybe belongs in a different module
def simplify_observations(observations: ResponseOrResults, align: bool = False) -> List[ResponseResult]:
    """Flatten out some nested data structures within observation records:

    * annotations
    * comments
    * identifications
    * non-owner IDs
    """
    return [_simplify_observation(o) for o in ensure_list(observations)]


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


def _format_model_objects(obj: ResponseOrResults, cls: Type[BaseModel], **kwargs):
    """Generic function to format a response, object, or list of objects"""
    objects = cls.from_json_list(obj)
    return '\n'.join([str(obj) for obj in objects])


# TODO: Figure out type annotations for these. Or just replace with pprint()?
format_identifications = partial(_format_model_objects, cls=Identification)
format_observations = partial(_format_model_objects, cls=Observation)
format_places = partial(_format_model_objects, cls=Place)
format_projects = partial(_format_model_objects, cls=Project)
format_search_results = partial(_format_model_objects, cls=SearchResult)
format_taxa = partial(_format_model_objects, cls=Taxon)
format_users = partial(_format_model_objects, cls=User)
