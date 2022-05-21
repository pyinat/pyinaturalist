"""Utilities for formatting API responses and model objects, for convenience/readability when exploring data.
Not used directly by API functions.

These functions will accept any of the following:

* A JSON response
* A list of response objects
* A single response object
"""
import json
from datetime import date, datetime, timedelta
from logging import basicConfig, getLogger
from typing import List, Mapping, Type

from requests import PreparedRequest, Response

from pyinaturalist.constants import DATETIME_SHORT_FORMAT, ResponseResult
from pyinaturalist.converters import ensure_list
from pyinaturalist.models import (
    Annotation,
    BaseModel,
    BaseModelCollection,
    Comment,
    ControlledTerm,
    ControlledTermCount,
    ControlledTermValue,
    Identification,
    LifeList,
    ListedTaxon,
    Message,
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
)
from pyinaturalist.paginator import Paginator


def enable_logging(level: str = 'INFO', external_level: str = 'WARNING'):
    """Configure logging to standard output with prettier tracebacks, formatting, and terminal
    colors (if supported).

    If you prefer, logging can be configured with the stdlib ``logging`` module instead; this just
    provides some convenient defaults.

    Args:
        level: Logging level to use for pyinaturalist
        external_level: Logging level to use for other libraries
    """
    from rich.logging import RichHandler

    basicConfig(
        format='%(message)s',
        datefmt='[%m-%d %H:%M:%S]',
        handlers=[RichHandler(rich_tracebacks=True, markup=True)],
        level=external_level,
    )
    getLogger('pyinaturalist').setLevel(level)
    getLogger('pyinaturalist_convert').setLevel(level)


# Default colors for table headers
HEADER_COLORS = {
    'Category': 'violet',
    'Comment': 'green',
    'Comments': 'blue',
    'Common name': 'blue',
    'Count': 'blue',
    'Created at': 'blue',
    'Date': 'blue',
    'Description': 'green',
    'Dimensions': 'blue',
    'Display name': 'violet',
    'Establishment means': 'violet',
    'From': 'magenta',
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
    'Subject': 'green',
    'Taxon ID': 'cyan',
    'Taxon': 'green',
    'Title': 'green',
    'To': 'magenta',
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
    'thread_id': Message,
    'body': Comment,  # Subset of ID attrs; if it's not an ID, assume it's a comment
    'multivalued': ControlledTerm,
    'controlled_value': ControlledTermCount,
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
        headers = {k: HEADER_COLORS.get(k, '') for k in values[0]._row.keys()}
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
        table.add_row(*[_str(value) for value in obj._row.values()])
    return table


def format_request(request: PreparedRequest, dry_run: bool = False) -> str:
    """Format HTTP request info"""
    headers = _format_headers(request.headers)
    body = _format_body(request.body)
    dry_run_str = ' (DRY RUN) ' if dry_run else ''
    return f'Request:{dry_run_str}\n{request.method} {request.url}\n{headers}\n{body}'


def format_response(response: Response) -> str:
    """Format HTTP response info, including whether it came from the cache"""
    headers = _format_headers(response.headers)
    error_msg = f' {response.text}' if not response.ok else ''

    def _expires_str():
        if response.expires:
            expires_delta = response.expires - datetime.utcnow()
            expires_delta -= timedelta(microseconds=expires_delta.microseconds)
            return f'expires in {expires_delta}'
        else:
            return 'never expires'

    cached = f'cached; {_expires_str()}' if getattr(response, 'from_cache', False) else 'not cached'
    return f'Response ({cached}):\n{response.status_code} {response.reason}{error_msg}\n{headers}'


def _format_headers(headers: Mapping[str, str]) -> str:
    ignore_headers = [
        'Access-Control-Allow-Headers',
        'Access-Control-Allow-Methods',
        'Access-Control-Allow-Origin',
        'X-Content-Type-Options',
    ]
    headers_dict = {k: v for k, v in headers.items() if k not in ignore_headers}
    if 'Authorization' in headers_dict:
        headers_dict['Authorization'] = '[REDACTED]'

    return '\n'.join([f'{k}: {v}' for k, v in headers_dict.items()])


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


# If rich is installed, install pretty-printer
try:
    from rich import pretty, print

    pretty.install()
except ImportError:
    pass
