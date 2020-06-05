from datetime import date, datetime
from typing import Dict, Any

from dateutil.parser import parse as parse_timestamp
from dateutil.tz import tzlocal
from pyinaturalist.constants import DATETIME_PARAMS
import pyinaturalist


# For Python < 3.5 compatibility
def merge_two_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z


def get_user_agent(user_agent: str = None) -> str:
    """Return the user agent to be used."""
    if user_agent is not None:  # If we explicitly provide one, use it
        return user_agent
    else:  # Otherwise we have a global one in __init__.py (configurable, with sensible defaults)
        return pyinaturalist.user_agent


def preprocess_request_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Perform type conversions, sanity checks, etc. on request parameters"""
    if not params:
        return {}

    params = convert_bool_params(params)
    params = convert_datetime_params(params)
    params = convert_list_params(params)
    params = strip_empty_params(params)
    return params


def convert_bool_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Convert any boolean request parameters to javascript-style boolean strings"""
    for k, v in params.items():
        if isinstance(v, bool):
            params[k] = str(v).lower()
    return params


def convert_datetime_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Convert any dates, datetimes, or timestamps in other formats into ISO 8601 strings.

    API behavior note: params that take date but not time info will accept a full timestamp and
    just ignore the time, so it's safe to parse both date and datetime strings into timestamps

    :raises: :py:exc:`dateutil.parser._parser.ParserError` if a date/datetime format is invalid
    """
    for k, v in params.items():
        if isinstance(v, datetime) or isinstance(v, date):
            params[k] = _isoformat(v)
        if k in DATETIME_PARAMS:
            params[k] = _isoformat(parse_timestamp(v))

    return params


def convert_list_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Convert any list parameters into an API-compatible (comma-delimited) string.
    Will be url-encoded by requests. For example: `['k1', 'k2', 'k3'] -> k1%2Ck2%2Ck3`
    """
    for k, v in params.items():
        if isinstance(v, list):
            params[k] = ",".join(map(str, v))
    return params


def strip_empty_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Remove any request parameters with empty or ``None`` values."""
    return {k: v for k, v in params.items() if v or v is False}


def _isoformat(d):
    """Return a date or datetime in ISO format.
    If it's a datetime and doesn't already have tzinfo, set it to the system's local timezone.
    """
    if isinstance(d, datetime) and not d.tzinfo:
        d = d.replace(tzinfo=tzlocal())
    return d.isoformat()
