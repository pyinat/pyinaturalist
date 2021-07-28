"""Helper functions for processing and validating request parameters.
The main purpose of these functions is to support some python-specific conveniences and translate
them into standard request parameters, along with request validation that makes debugging easier.
"""
from datetime import date, datetime
from logging import getLogger
from typing import Any, Iterable, List, Optional, Tuple

from dateutil.relativedelta import relativedelta

from pyinaturalist.constants import *  # noqa: F401, F403  # Imports for backwards-compatibility
from pyinaturalist.constants import (
    DATETIME_PARAMS,
    MULTIPLE_CHOICE_PARAMS,
    RANKS,
    MultiInt,
    RequestParams,
)
from pyinaturalist.converters import (
    convert_csv_list,
    convert_isoformat,
    ensure_list,
    strip_empty_values,
    try_int,
)

MULTIPLE_CHOICE_ERROR_MSG = (
    'Parameter "{}" must have one of the following values: {}\n\tValue provided: {}'
)

logger = getLogger(__name__)


def preprocess_request_body(body: Optional[RequestParams]) -> RequestParams:
    """Perform type conversions, sanity checks, etc. on JSON-formatted request body"""
    if not body:
        return {}
    if 'observation' in body:
        body['observation'] = preprocess_request_params(body['observation'])
    else:
        body = preprocess_request_params(body)
    return body


def preprocess_request_params(params: Optional[RequestParams]) -> RequestParams:
    """Perform type conversions, sanity checks, etc. on request parameters"""
    if not params:
        return {}

    params = validate_multiple_choice_params(params)
    params = convert_pagination_params(params)
    params = convert_bool_params(params)
    params = convert_datetime_params(params)
    params = convert_list_params(params)
    params = strip_empty_values(params)
    return params


def convert_bool_params(params: RequestParams) -> RequestParams:
    """Convert any boolean request parameters to javascript-style boolean strings"""
    for k, v in params.items():
        if isinstance(v, bool):
            params[k] = str(v).lower()
    return params


def convert_url_ids(url: str, ids: MultiInt = None) -> str:
    """If one or more resources are requested by ID, validate and update the request URL accordingly"""
    if ids:
        url = url.rstrip('/') + '/' + validate_ids(ids)
    return url


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
    return {k: convert_csv_list(v) for k, v in params.items()}


def convert_observation_fields(params: RequestParams) -> RequestParams:
    """Translate simplified format of observation field values into API-compatible format"""
    if 'observation_fields' in params:
        params['observation_field_values_attributes'] = params.pop('observation_fields')
    obs_fields = params.get('observation_field_values_attributes')
    if isinstance(obs_fields, dict):
        params['observation_field_values_attributes'] = [
            {'observation_field_id': k, 'value': v} for k, v in obs_fields.items()
        ]
    return params


def convert_pagination_params(params: RequestParams) -> RequestParams:
    """Allow ``count_only=True`` as a slightly more intuitive shortcut to only get a count of
    results"""
    if params.pop('count_only', None) is True:
        params['per_page'] = 0
    return params


def convert_rank_range(params: RequestParams) -> RequestParams:
    """If min and/or max rank is specified in params, translate into a list of ranks"""

    def _get_rank_index(rank: str) -> int:
        if rank not in RANKS:
            raise ValueError('Invalid rank')
        return RANKS.index(rank)

    min_rank, max_rank = params.pop('min_rank', None), params.pop('max_rank', None)
    if min_rank or max_rank:
        # Use indices in RANKS list to determine range of ranks to include
        min_rank_index = _get_rank_index(min_rank) if min_rank else 0
        max_rank_index = _get_rank_index(max_rank) + 1 if max_rank else len(RANKS)
        params['rank'] = RANKS[min_rank_index:max_rank_index]
    return params


def get_interval_ranges(
    start_date: datetime, end_date: datetime, interval='monthly'
) -> List[Tuple[datetime, datetime]]:
    """Get a list of date ranges between ``start_date`` and ``end_date`` with the specified interval
    Example:
        >>> # Get date ranges representing months of a year
        >>> get_interval_ranges(datetime(2020, 1, 1), datetime(2020, 12, 31), 'monthly')

    Args:
        start_date: Starting date of date ranges (inclusive)
        end_date: End date of date ranges (inclusive)
        interval: Either 'monthly' or 'yearly'

    Returns:
        List of date ranges in the format: ``[(start_date, end_date), (start_date, end_date), ...]``
    """
    if interval == 'monthly':
        delta = relativedelta(months=1)
    elif interval == 'yearly':
        delta = relativedelta(years=1)
    else:
        raise ValueError(f'Invalid interval: {interval}')

    incremental_date = start_date
    interval_ranges = []
    while incremental_date <= end_date:
        interval_ranges.append((incremental_date, incremental_date + delta - relativedelta(days=1)))
        incremental_date += delta
    return interval_ranges


def is_int_list(values: Any) -> bool:
    """Determine if a value contains one or more valid integers"""
    return all([try_int(v) is not None for v in ensure_list(values, convert_csv=True)])


def validate_ids(ids: Any) -> str:
    """Ensure ID(s) are all valid integers, and convert to a comma-delimited string if multiple

    Raises:
        :py:exc:`ValueError` if any values are not valid integers
    """
    if not is_int_list(ids):
        raise ValueError(f'Invalid ID(s): {ids}; must specify integers only')
    return convert_csv_list([int(id) for id in ensure_list(ids, convert_csv=True)])


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


def validate_multiple_choice_param(params: RequestParams, key: str, choices: Iterable) -> RequestParams:
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
        return all([v in choices for v in value])

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
