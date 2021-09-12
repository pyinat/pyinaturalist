# TODO: Make rich a required dependency for 0.16
"""Utilities for formatting API responses and model objects, for convenience/readability when exploring data.
Not used directly by API functions.

These functions will accept any of the following:

* A JSON response
* A list of response objects
* A single response object
"""
import json
from copy import deepcopy
from datetime import date, datetime
from functools import partial
from logging import basicConfig, getLogger
from typing import Any, Iterable, List, Type

from attr import Attribute
from requests import PreparedRequest

from pyinaturalist.constants import DATETIME_SHORT_FORMAT, ResponseOrResults, ResponseResult
from pyinaturalist.converters import ensure_list
from pyinaturalist.models import (
    Annotation,
    BaseModel,
    BaseModelCollection,
    Comment,
    ControlledTerm,
    ControlledTermValue,
    Identification,
    LifeList,
    ListedTaxon,
    Observation,
    ObservationField,
    ObservationFieldValue,
    Photo,
    Place,
    Project,
    ResponseOrObjects,
    SearchResult,
    Taxon,
    TaxonCount,
    TaxonSummary,
    User,
    get_lazy_attrs,
)
from pyinaturalist.paginator import Paginator


def enable_logging(level: str = 'INFO'):
    """Configure logging to standard output with prettier tracebacks and terminal colors (if supported).
    Logging can of course be configured however you want using the stdlib ``logging`` module; this is
    just here for convenience.

    Args:
        level: Logging level to use
    """
    from rich.logging import RichHandler

    basicConfig(
        format='%(message)s',
        datefmt='[%m-%d %H:%M:%S]',
        handlers=[RichHandler(rich_tracebacks=True, markup=True)],
    )
    getLogger('pyinaturalist').setLevel(level)


# Default colors for table headers
HEADER_COLORS = {
    'Category': 'violet',
    'Comment': 'green',
    'Comments': 'blue',
    'Common name': 'blue',
    'Count': 'blue',
    'Created at': 'blue',
    'Description': 'green',
    'Dimensions': 'blue',
    'Display name': 'violet',
    'Establishment means': 'violet',
    'From CV': 'white',
    'Identifications': 'blue',
    'ID': 'cyan',
    'Label': 'green',
    'Latitude': 'blue',
    'License': 'green',
    'Life list': 'green',
    'Location': 'white',
    'Longitude': 'blue',
    'Name': 'magenta',
    'Observations': 'blue',
    'Observed on': 'blue',
    'Place ID': 'cyan',
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
    'body': Comment,  # Subset of ID attrs; if it's not an ID, assume it's a comment
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
    'last_observation_id': ListedTaxon,
    'listed_taxon': TaxonSummary,
    'count': TaxonCount,
    'rank': Taxon,
    'roles': User,
}


def pprint(values: ResponseOrObjects):
    """Pretty-print any model object or list into a condensed summary.

    **Experimental:** May also be used on most raw JSON API responses
    """
    try:
        print(format_table(values))
    except ValueError:
        print(values)


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
    if isinstance(values, Paginator):
        return values.all()

    values = ensure_list(values)
    if isinstance(values, BaseModelCollection) or isinstance(values[0], BaseModel):
        return values  # type: ignore

    cls = detect_type(values[0])
    return [cls.from_json(value) for value in values]


def format_table(values: ResponseOrObjects):
    """Format model objects as a table. If ``rich`` isn't installed or the model doesn't have a
    table format defined, just return a basic list of stringified objects.
    """
    try:
        from rich.box import SIMPLE_HEAVY
        from rich.table import Column, Table

        if isinstance(values, Table):
            return values

        values = ensure_model_list(values)
        headers = {k: HEADER_COLORS.get(k, '') for k in values[0].row.keys()}
    except (ImportError, NotImplementedError):
        return '\n'.join([str(obj) for obj in ensure_model_list(values)])

    # Display any date/datetime values in short format
    def _str(value):
        if isinstance(value, (date, datetime)):
            return value.strftime(DATETIME_SHORT_FORMAT)
        return str(value) if value is not None else ''

    columns = [Column(header, style=style) for header, style in headers.items()]
    table = Table(*columns, box=SIMPLE_HEAVY, header_style='bold white', row_styles=['dim', 'none'])

    for obj in values:
        table.add_row(*[_str(value) for value in obj.row.values()])
    return table


def format_request(request: PreparedRequest, dry_run: bool = False) -> str:
    """Format HTTP request info"""
    headers_dict = request.headers.copy()
    if 'Authorization' in headers_dict:
        headers_dict['Authorization'] = '[REDACTED]'

    headers = '\n'.join([f'{k}: {v}' for k, v in headers_dict.items()])
    body = _format_body(request.body)
    dry_run_str = '(DRY RUN) ' if dry_run else ''
    return f'{dry_run_str}{request.method} {request.url}\n{headers}\n{body}'


def _format_body(body):
    if not body:
        return ''
    try:
        body = json.loads(body)
        for key in ['password', 'client_secret']:
            if key in body:
                body[key] = '[REDACTED]'
        return body
    except Exception:
        return '(non-JSON request body)'


# TODO: This maybe belongs in a different module
def simplify_observations(
    observations: ResponseOrResults, align: bool = False
) -> List[ResponseResult]:
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


format_controlled_terms = partial(_format_model_objects, cls=ControlledTerm)
format_identifications = partial(_format_model_objects, cls=Identification)
format_observations = partial(_format_model_objects, cls=Observation)
format_places = partial(_format_model_objects, cls=Place)
format_projects = partial(_format_model_objects, cls=Project)
format_search_results = partial(_format_model_objects, cls=SearchResult)
format_species_counts = partial(_format_model_objects, cls=TaxonCount)
format_taxa = partial(_format_model_objects, cls=Taxon)
format_users = partial(_format_model_objects, cls=User)


def get_model_fields(obj: Any) -> Iterable[Attribute]:
    """Modification for rich's pretty-printer (specifically, ``rich.pretty._get_attr_fields``).

    Adds placeholder attributes for lazy-loaded model properties so they get included in the output.
    This is particularly useful for previewing in Jupyter or another REPL. These nested objects are
    shown in condensed format so the preview is more readable. Otherwise, some objects]
    (especially observations) can turn into a huge wall of text several pages long.

    Does not change behavior for anything except :py:class:`.BaseModel` subclasses.
    """

    def condense_nested_models(obj):
        tab = '    '
        if obj and isinstance(obj, list):
            condensed_objs = f',\n{tab}{tab}'.join([str(o) for o in obj])
            return f'[\n{tab}{tab}{condensed_objs}\n{tab}]'
        return str(obj)

    attrs = list(obj.__attrs_attrs__)
    if isinstance(obj, BaseModel):
        attrs += get_lazy_attrs(obj, repr=condense_nested_models)
    return attrs


# If rich is installed, update its pretty-printer to include model properties
try:
    from rich import pretty, print

    pretty._get_attr_fields = get_model_fields
    pretty.install()
except ImportError:
    pass
