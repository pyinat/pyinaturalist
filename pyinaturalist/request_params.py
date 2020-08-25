""" Helper functions for processing request parameters """
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from warnings import warn

from dateutil.parser import parse as parse_timestamp
from dateutil.tz import tzlocal
from pyinaturalist.constants import (
    CC_LICENSES,
    COMMUNITY_ID_STATUSES,
    CONSERVATION_STATUSES,
    DATETIME_PARAMS,
    EXTRA_PROPERTIES,
    GEOPRIVACY_LEVELS,
    HAS_PROPERTIES,
    ICONIC_TAXA,
    RANKS,
    ORDER_BY_PROPERTIES,
    ORDER_DIRECTIONS,
    SEARCH_PROPERTIES,
    QUALITY_GRADES,
)

# Multiple-choice request parameters and their possible choices
MULTIPLE_CHOICE_PARAMS = {
    "csi": CONSERVATION_STATUSES,
    "extra": EXTRA_PROPERTIES,
    "geoprivacy": GEOPRIVACY_LEVELS,
    "has": HAS_PROPERTIES,
    "hrank": RANKS,
    "iconic_taxa": ICONIC_TAXA.values(),
    "identifications": COMMUNITY_ID_STATUSES,
    "license": CC_LICENSES,
    "lrank": RANKS,
    "max_rank": RANKS,
    "min_rank": RANKS,
    "order": ORDER_DIRECTIONS,
    "order_by": ORDER_BY_PROPERTIES,
    "photo_license": CC_LICENSES,
    "quality_grade": QUALITY_GRADES,
    "rank": RANKS,
    "search_on": SEARCH_PROPERTIES,
    "sound_license": CC_LICENSES,
    "taxon_geoprivacy": GEOPRIVACY_LEVELS,
}


def check_deprecated_params(params, **kwargs) -> Dict[str, Any]:
    if params:
        warn(
            DeprecationWarning(
                "The 'params' argument is deprecated; please use keyword arguments instead"
            )
        )
        kwargs.update(params)
    return kwargs


def preprocess_request_params(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """ Perform type conversions, sanity checks, etc. on request parameters """
    if not params:
        return {}

    validate_multiple_choice_params(params)
    params = convert_bool_params(params)
    params = convert_datetime_params(params)
    params = convert_list_params(params)
    params = strip_empty_params(params)
    return params


def is_int(value: Any) -> bool:
    """ Determine if a value is a valid integer """
    try:
        int(value)
        return True
    except (TypeError, ValueError):
        return False


def is_int_list(values: Any) -> bool:
    """ Determine if a value is a list of valid integers """
    return isinstance(values, list) and all([is_int(v) for v in values])


def convert_bool_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """ Convert any boolean request parameters to javascript-style boolean strings """
    for k, v in params.items():
        if isinstance(v, bool):
            params[k] = str(v).lower()
    return params


def convert_datetime_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """ Convert any dates, datetimes, or timestamps in other formats into ISO 8601 strings.

    API behavior note: params that take date but not time info will accept a full timestamp and
    just ignore the time, so it's safe to parse both date and datetime strings into timestamps

    :raises: :py:exc:`dateutil.parser._parser.ParserError` if a date/datetime format is invalid
    """
    for k, v in params.items():
        if isinstance(v, datetime) or isinstance(v, date):
            params[k] = _isoformat(v)
        if v is not None and k in DATETIME_PARAMS:
            params[k] = _isoformat(parse_timestamp(v))

    return params


def convert_list_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """ Convert any list parameters into an API-compatible (comma-delimited) string.
    Will be url-encoded by requests. For example: `['k1', 'k2', 'k3'] -> k1%2Ck2%2Ck3`
    """
    return {k: convert_list(v) for k, v in params.items()}


def convert_list(obj) -> str:
    """ Convert a list parameters into an API-compatible (comma-delimited) string """
    if not obj:
        return ""
    if isinstance(obj, list):
        return ",".join(map(str, obj))
    return str(obj)


def strip_empty_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """ Remove any request parameters with empty or ``None`` values."""
    return {k: v for k, v in params.items() if v or v is False}


def validate_multiple_choice_params(params: Dict):
    """ Verify that all multiple-choice request parameters contain a valid value

    Raises:
        :py:exc:`ValueError`
    """

    def _validate_multiple_choice_param(key, value):
        if not value:
            return True
        if not isinstance(value, list):
            value = [value]
        return all([v in MULTIPLE_CHOICE_PARAMS[key] for v in value])

    errors = []
    for param, choices in MULTIPLE_CHOICE_PARAMS.items():
        if param in params and not _validate_multiple_choice_param(param, params[param]):
            errors.append(
                "Parameter '{}' must have one of the following values: {}".format(param, choices)
                + " Value provided: {}".format(params[param])
            )

    if errors:
        raise ValueError("\n".join(errors))


def _isoformat(d):
    """Return a date or datetime in ISO format.
    If it's a datetime and doesn't already have tzinfo, set it to the system's local timezone.
    """
    if isinstance(d, datetime) and not d.tzinfo:
        d = d.replace(tzinfo=tzlocal())
    return d.isoformat()


def translate_rank_range(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    if kwargs.get("min_rank") or kwargs.get("max_rank"):
        kwargs["rank"] = _get_rank_range(kwargs.pop("min_rank", None), kwargs.pop("max_rank", None))
    return kwargs


def _get_rank_range(min_rank: str = None, max_rank: str = None) -> List[str]:
    """ Translate min and/or max rank into a list of ranks """

    def _get_rank_index(rank: str) -> int:
        if rank not in RANKS:
            raise ValueError("Invalid rank")
        return RANKS.index(rank)

    min_rank_index = _get_rank_index(min_rank) if min_rank else 0
    max_rank_index = _get_rank_index(max_rank) + 1 if max_rank else len(RANKS)
    return RANKS[min_rank_index:max_rank_index]
