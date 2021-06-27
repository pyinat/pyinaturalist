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
from typing import Callable, List, Type

from pyinaturalist.constants import ResponseOrResults, ResponseResult
from pyinaturalist.converters import ensure_list
from pyinaturalist.models import (
    Annotation,
    BaseModel,
    Comment,
    ControlledTerm,
    ControlledTermValue,
    Identification,
    LifeList,
    Observation,
    ObservationField,
    ObservationFieldValue,
    Photo,
    Place,
    Project,
    ResponseOrObjects,
    SearchResult,
    Taxon,
    User,
    get_model_fields,
)

# If rich is installed, update its pretty-printer to include model properties
try:
    from rich import pretty, print

    pretty._get_attr_fields = get_model_fields
    pretty.install()
except ImportError:
    pass


# Default colors for table headers
HEADER_COLORS = {
    'Category': 'violet',
    'Comment': 'green',
    'Common name': 'blue',
    'Count': 'blue',
    'Created at': 'blue',
    'Description': 'green',
    'Dimensions': 'blue',
    'Display name': 'violet',
    'From CV': 'white',
    'ID count': 'blue',
    'ID': 'cyan',
    'Label': 'green',
    'Latitude': 'blue',
    'License': 'green',
    'Location': 'white',
    'Longitude': 'blue',
    'Name': 'magenta',
    'Obs. count': 'blue',
    'Observed on': 'blue',
    'Rank': 'violet',
    'Scientific name': 'green',
    'Score': 'green',
    'Taxon ID': 'cyan',
    'Taxon': 'green',
    'Title': 'green',
    'Type': 'blue',
    'URL': 'white',
    'User': 'magenta',
    'Username': 'magenta',
    'Value': 'green',
    'Votes': 'blue',
}

# Unique response attributes used to auto-detect response types
UNIQUE_RESPONSE_ATTRS = {
    'vote_score': Annotation,
    'disagreement': Identification,
    'moderator_actions': Comment,  # Subset of ID attrs; if it's not an ID, assume it's a comment
    'multivalued': ControlledTerm,
    'blocking': ControlledTermValue,
    'count_without_taxon': LifeList,
    'captive': Observation,
    'allowed_values': ObservationField,
    'field_id': ObservationFieldValue,
    'original_dimensions': Photo,
    'place_type': Place,
    'standard': Place,
    'project_type': Project,
    'score': SearchResult,
    'rank': Taxon,
    'roles': User,
}


def pprint(values: ResponseOrObjects):
    """Pretty-print any model object or list into a condensed summary.

    **Experimental:** May also be used on most raw JSON API responses
    """
    print(format_table(values))


def detect_type(value: ResponseResult) -> Type[BaseModel]:
    """Attempt to determine the model class corresponding to an API result"""
    for key, cls in UNIQUE_RESPONSE_ATTRS.items():
        if key in value:
            return cls

    raise ValueError(f'Could not detect response type: {value}')


def ensure_model_list(values: ResponseOrObjects) -> List[BaseModel]:
    """If the given values are raw JSON responses, attempt to detect their type and convert to
    model objects
    """
    if isinstance(values, LifeList):
        return values.taxa  # type: ignore
    values = ensure_list(values)
    if isinstance(values[0], BaseModel):
        return values

    cls = detect_type(values[0])
    return [cls.from_json(value) for value in values]


def format_table(values: ResponseOrObjects):
    """Format model objects as a table. If ``rich`` isn't installed or the model doesn't have a
    table format defined, just return a basic list of stringified objects.
    """
    values = ensure_model_list(values)

    try:
        from rich.box import SIMPLE_HEAVY
        from rich.table import Column, Table

        headers = {k: HEADER_COLORS.get(k, '') for k in values[0].row.keys()}
    except (ImportError, NotImplementedError):
        return '\n'.join([str(obj) for obj in values])

    # Display any date/datetime values in short format
    def _str(value):
        if isinstance(value, (date, datetime)):
            return value.strftime('%b %d, %Y')
        return str(value) if value is not None else ''

    columns = [Column(header, style=style) for header, style in headers.items()]
    table = Table(*columns, box=SIMPLE_HEAVY, header_style='bold white', row_styles=['dim', 'none'])

    for obj in values:
        table.add_row(*[_str(value) for value in obj.row.values()])
    return table


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
format_controlled_terms = partial(_format_model_objects, cls=ControlledTerm)
format_identifications = partial(_format_model_objects, cls=Identification)
format_observations = partial(_format_model_objects, cls=Observation)
format_places = partial(_format_model_objects, cls=Place)
format_projects = partial(_format_model_objects, cls=Project)
format_search_results = partial(_format_model_objects, cls=SearchResult)
format_taxa = partial(_format_model_objects, cls=Taxon)
format_users = partial(_format_model_objects, cls=User)
