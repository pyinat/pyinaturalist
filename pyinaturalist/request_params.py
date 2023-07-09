"""Helper functions for processing and validating request parameters.
The main purpose of these functions is to support some python-specific conveniences and translate
them into standard API request parameters, along with client-side request validation.

Also see :py:mod:`pyinaturalist.converters` for type conversion utilities not specific to request
params.
"""
import re
from datetime import date, datetime, timedelta
from inspect import signature
from logging import getLogger
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Tuple, Union

from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta

from pyinaturalist.constants import *  # noqa: F401, F403  # Imports for backwards-compatibility
from pyinaturalist.constants import (
    DATETIME_PARAMS,
    MULTIPLE_CHOICE_PARAMS,
    RANK_EQUIVALENTS,
    RANKS,
    DateOrStr,
    DateRange,
    MultiInt,
    RequestParams,
    TimeInterval,
)
from pyinaturalist.converters import convert_isoformat, ensure_list

# Common parameters that can be passed to all API functions, and notes on where they are used
COMMON_PARAMS = [
    'access_token',  # Used in session.prepare_request()
    'allow_str_ids',  # Used in session.prepare_request()
    'dry_run',  # Used in session.request()
    'expire_after',  # Passed to requests_cache.CachedSession.send()
    'limit',  # Used in paginator.Paginator
    'session',  # Used in session.request()
    'timeout',  # Used in session.ClientSession.send()
    'user_agent',  # Used in session.prepare_request()
]

# Time interval options used by observation histogram
INTERVALS: Dict[str, Union[timedelta, relativedelta]] = {
    'hour': timedelta(hours=1),
    'day': timedelta(days=1),
    'week': relativedelta(weeks=1),
    'month': relativedelta(months=1),
    'year': relativedelta(years=1),
}

RANK_PARAMS = [
    'rank',
    'lrank',
    'hrank',
    'min_rank',
    'max_rank',
    'observation_rank',
    'observation_lrank',
    'observation_hrank',
]

MULTIPLE_CHOICE_ERROR_MSG = (
    'Parameter "{}" must have one of the following values: {}\n\tValue provided: {}'
)

MAX_URL_LENGTH = 2048  # Depends on server and browser. This is is on the lower end.

logger = getLogger(__name__)


def preprocess_request_body(body: Optional[RequestParams]) -> Optional[RequestParams]:
    """Perform type conversions, sanity checks, etc. on JSON-formatted request body"""
    if not body:
        return None
    for resource in ['project', 'observation']:
        if resource in body:
            body[resource] = preprocess_request_params(body[resource], convert_lists=False)
    else:
        body = preprocess_request_params(body, convert_lists=False)
    return body


def preprocess_request_params(
    params: Optional[RequestParams], convert_lists: bool = True
) -> RequestParams:
    """Perform type conversions, sanity checks, etc. on request parameters"""
    if not params:
        return {}

    params = normalize_rank_params(params)
    params = validate_multiple_choice_params(params)
    params = convert_pagination_params(params)
    params = convert_bool_params(params)
    params = convert_datetime_params(params)
    params = convert_observation_field_filters(params)
    if convert_lists:
        params = convert_list_params(params)
    params = strip_empty_values(params)
    params, _ = split_common_params(params)
    return params


def convert_bool_params(params: RequestParams) -> RequestParams:
    """Convert any boolean request parameters to javascript-style boolean strings"""
    for k, v in params.items():
        if isinstance(v, bool):
            params[k] = str(v).lower()
    return params


def convert_url_ids(url: str, ids: Optional[MultiInt] = None, allow_str_ids: bool = False) -> str:
    """If one or more resources are requested by ID, validate and update the request URL
    accordingly"""
    if not ids:
        return url
    if not allow_str_ids:
        ids = _validate_ids(ids)
    return url.rstrip('/') + '/' + _join_list(ids)


def _join_list(obj: Any) -> str:
    """Join a list of items into an API-compatible (comma-delimited) string"""
    if isinstance(obj, list) or isinstance(obj, tuple):
        return ','.join(map(str, obj))
    elif obj is None:
        return ''
    else:
        return str(obj)


def _validate_ids(ids: Any) -> List[int]:
    """Ensure ID(s) are all valid, and convert to a comma-delimited string if there are multiple

    Raises:
        :py:exc:`ValueError` if any values are not valid integers
    """
    try:
        return [int(value) for value in ensure_list(ids, split_str_list=True)]
    except (TypeError, ValueError) as e:
        raise ValueError(f'Invalid ID(s): {ids}; must specify integers only') from e


def convert_datetime_params(params: RequestParams) -> RequestParams:
    """Convert any dates, datetimes, or timestamps in other formats into ISO 8601 strings.

    API behavior note: params that take date but not time info will accept a full timestamp and
    just ignore the time, so it's safe to parse both date and datetime strings into timestamps

    Raises:
        :py:exc:`dateutil.parser._parser.ParserError` if a date/datetime format is invalid
    """
    for k, v in params.items():
        if isinstance(v, (date, datetime)) or (isinstance(v, str) and k in DATETIME_PARAMS):
            params[k] = convert_isoformat(v)
    return params


def convert_list_params(params: RequestParams) -> RequestParams:
    """Convert any list parameters into an API-compatible (comma-delimited) string.
    Will be url-encoded by requests. For example: `['k1', 'k2', 'k3'] -> k1%2Ck2%2Ck3`
    """
    return {k: _join_list(v) for k, v in params.items()}


def convert_observation_params(params):
    """Some common parameter conversions needed by observation CRUD endpoints"""
    params = convert_observation_field_params(params)
    if params.get('observed_on'):
        params['observed_on_string'] = params.pop('observed_on')

    # Split out photos and sounds to upload separately
    photos = ensure_list(params.pop('local_photos', None))
    photos.extend(ensure_list(params.pop('photos', None)))  # Alias for 'local_photos'
    sounds = ensure_list(params.pop('sounds', None))
    photo_ids = ensure_list(params.pop('photo_ids', None))

    # Split API request params from common function args
    params, kwargs = split_common_params(params)

    # ignore_photos must be 1 rather than true; 0 does not work, so just remove if false
    if params.pop('ignore_photos', True):
        kwargs['ignore_photos'] = 1

    return photos, sounds, photo_ids, params, kwargs


def convert_observation_field_params(params: RequestParams) -> RequestParams:
    """Translate simplified format of observation field values into API-compatible format"""
    if 'observation_fields' in params:
        params['observation_field_values_attributes'] = params.pop('observation_fields')
    obs_fields = params.get('observation_field_values_attributes')
    if isinstance(obs_fields, dict):
        params['observation_field_values_attributes'] = [
            {'observation_field_id': k, 'value': v} for k, v in obs_fields.items()
        ]
    return params


def convert_observation_field_filters(params: RequestParams) -> RequestParams:
    """Convert observation field filters from simplified format to full request params"""
    fields = params.pop('observation_fields', None)
    if not fields:
        return params
    # List of fields to filter on (any value)
    elif isinstance(fields, (list, tuple)):
        for field in fields:
            params[f'field:{field}'] = ''
    # List of fields to filter on (specific values)
    elif isinstance(fields, Mapping):
        for field, value in fields.items():
            params[f'field:{field}'] = value or ''
    return params


def convert_pagination_params(params: RequestParams) -> RequestParams:
    """Allow ``count_only=True`` as a slightly more intuitive shortcut to only get a count of
    results"""
    if params.pop('count_only', False) is True:
        params['per_page'] = 0
    if params.pop('reverse', False) is True:
        params['order'] = 'descending'
    return params


def convert_rank_range(params: RequestParams) -> RequestParams:
    """If min and/or max rank is specified in params, translate into a list of ranks"""

    def _get_rank_index(rank: str) -> int:
        rank = normalize_rank(rank)
        if rank not in RANKS:
            raise ValueError(f'Invalid rank: {rank}')
        return RANKS.index(rank)

    min_rank, max_rank = params.pop('min_rank', None), params.pop('max_rank', None)
    if min_rank or max_rank:
        # Use indices in RANKS list to determine range of ranks to include
        min_rank_index = _get_rank_index(min_rank) if min_rank else 0
        max_rank_index = _get_rank_index(max_rank) + 1 if max_rank else len(RANKS)
        params['rank'] = RANKS[min_rank_index:max_rank_index]
    return params


def normalize_rank(rank: str) -> str:
    """Normalize and validate a taxonomic rank, alias, or abbreviation"""
    rank = re.sub(r'[-_\.\s]', '', rank).lower()

    # Check if it's an alias/equivalent rank that iNaturalist accepts
    if rank in RANK_EQUIVALENTS:
        rank = RANK_EQUIVALENTS[rank]
    # Check if it's a unique prefix of a rank
    elif rank not in RANKS:
        matching_ranks = [r for r in RANKS if r.startswith(rank)]
        rank = matching_ranks[0] if len(matching_ranks) == 1 else rank

    return rank


def normalize_rank_params(params: RequestParams) -> RequestParams:
    """Normalize any taxonomic ranks in request params"""
    for k in RANK_PARAMS:
        if isinstance(params.get(k), (tuple, list)):
            params[k] = [normalize_rank(r) for r in params[k]]
        elif params.get(k):
            params[k] = normalize_rank(params[k])
    return params


def get_interval_ranges(
    start: DateOrStr, end: DateOrStr, interval: TimeInterval
) -> List[DateRange]:
    """Given a date range and a time interval, split the range into a list of smaller ranges

    Args:
        start: Start date or string (inclusive)
        end: End date or string (inclusive)
        interval: Time interval (delta or alias: 'hour', 'day', 'month', or 'year')

    Returns:
        List of date ranges of size ``interval``, in the format: ``[(start_date, end_date), ...]``
    """
    if isinstance(interval, str):
        interval = INTERVALS[interval]
    if isinstance(start, str):
        start = parse_date(start)
    if isinstance(end, str):
        end = parse_date(end)

    ranges = []
    while start <= end:
        # API date/datetime request params are inclusive, so subtract 1 minute from end date
        ranges.append((start, start + interval - timedelta(minutes=1)))
        start += interval
    return ranges


def get_valid_kwargs(func: Callable, kwargs: Dict) -> Dict:
    """Get the subset of non-None ``kwargs`` that are valid params for ``func``"""
    sig_params = list(signature(func).parameters)
    return {k: v for k, v in kwargs.items() if k in sig_params and v is not None}


def split_common_params(params: RequestParams) -> Tuple[RequestParams, RequestParams]:
    """Split out common keyword args (for pyinaturalist functions) from request params (for API)"""
    kwargs = {k: params.pop(k, None) for k in COMMON_PARAMS}
    return params, kwargs


def strip_empty_values(values: Dict) -> Dict:
    """Remove any dict items with empty or ``None`` values.
    Observation field fiters are an exception (e.g. ``field:foo=``).
    """
    return {k: v for k, v in values.items() if v or v in [False, 0, 0.0] or k.startswith('field:')}


def validate_multiple_choice_params(params: RequestParams) -> RequestParams:
    """Verify that multiple-choice request parameters contain a valid value.

    **Note:** This does not check endpoint-specific params, i.e., those that have the same name
    but different values across different endpoints.

    Returns:
        Parameters with modifications (if any)

    Raises:
        :py:exc:`ValueError`;
            Error message will contain info on all validation errors, if there are multiple
    """
    # Collect info on any validation errors
    errors = []
    for key, choices in MULTIPLE_CHOICE_PARAMS.items():
        params, error_msg = _validate_multiple_choice_param(params, key, choices)
        if error_msg:
            errors.append(error_msg)

    # Combine all messages (if multiple) into one error message
    if errors:
        raise ValueError('\n'.join(errors))
    return params


def validate_multiple_choice_param(
    params: RequestParams, key: str, choices: Iterable
) -> RequestParams:
    """Verify that a multiple-choice request parameter contains valid value(s);
    if not, raise an error.
    **Used for endpoint-specific params.**

    Returns:
        Parameters with modifications (if any)

    Raises:
        :py:exc:`ValueError`
    """
    params, error_msg = _validate_multiple_choice_param(params, key, choices)
    if error_msg:
        raise ValueError(error_msg)
    return params


def _validate_multiple_choice_param(
    params: RequestParams, key: str, choices: Iterable
) -> Tuple[RequestParams, Optional[str]]:
    """Verify that a multiple-choice request parameter contains valid value(s);
    if not, return an error message.

    Returns:
        Parameters with modifications (if any), and a validation error message (if any)
    """

    def is_valid(value, choices):
        if not value:
            return True
        if not isinstance(value, list):
            value = [value]
        return all(v in choices for v in value)

    def normalize(value):
        if not value:
            return value
        if isinstance(value, list):
            return [v.replace(' ', '_') for v in value]
        return value.replace(' ', '_')

    error_msg = None
    if key in params:
        params[key] = normalize(params[key])
    if not is_valid(params.get(key), choices):
        error_msg = MULTIPLE_CHOICE_ERROR_MSG.format(key, choices, params[key])
    return params, error_msg


def batch_ids(base_url: str, ids: Iterable[int]) -> Iterable[List[int]]:
    """Split IDs into batches that are small enough to fit in a single URL."""
    length_remaining = MAX_URL_LENGTH - len(base_url)
    batch: List[int] = []
    for id in ids:
        length = len(str(id)) + 1
        if length > length_remaining:
            yield batch
            batch = []
            length_remaining = MAX_URL_LENGTH - len(base_url)
        batch.append(id)
        length_remaining -= length

    if batch:
        yield batch
