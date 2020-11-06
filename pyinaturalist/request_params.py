"""Helper functions for processing and validating request parameters"""
from datetime import date, datetime
from io import BytesIO
from logging import getLogger
from os.path import abspath, expanduser
from typing import Any, BinaryIO, Dict, Iterable, Optional
import warnings

from dateutil.parser import parse as parse_timestamp
from dateutil.tz import tzlocal
from pyinaturalist.constants import FileOrPath, RequestParams


# Basic observation attributes to include by default in geojson responses
DEFAULT_OBSERVATION_ATTRS = [
    "id",
    "photo_url",
    "positional_accuracy",
    "preferred_common_name",
    "quality_grade",
    "taxon_id",
    "taxon_name",
    "time_observed_at",
    "uri",
]

# All request parameters from both Node API and REST (Rails) API that accept date or datetime strings
DATETIME_PARAMS = [
    "created_after",
    "created_d1",
    "created_d2",
    "created_on",
    "d1",
    "d2",
    "newer_than",
    "observation_created_d1",
    "observation_created_d2",
    "observed_d1",
    "observed_d2",
    "observed_on",
    "older_than",
    "on",
    "since",
    "updated_since",  # TODO: test if this one behaves differently in Node API vs REST API
]

# Reponse formats supported by GET /observations endpoint
OBSERVATION_FORMATS = ["atom", "csv", "dwc", "json", "kml", "widget"]

# Creative Commons license codes
CC_LICENSES = ["CC-BY", "CC-BY-NC", "CC-BY-ND", "CC-BY-SA", "CC-BY-NC-ND", "CC-BY-NC-SA", "CC0"]

# IUCN Conservation status codes; for more info, see: https://www.iucnredlist.org
CONSERVATION_STATUSES = ["LC", "NT", "VU", "EN", "CR", "EW", "EX"]

# Taxon ID and name of main taxa "categories" that can be filtered on
ICONIC_TAXA = {
    0: "Unknown",
    1: "Animalia",
    3: "Aves",
    20978: "Amphibia",
    26036: "Reptilia",
    40151: "Mammalia",
    47178: "Actinopterygii",
    47115: "Mollusca",
    47119: "Arachnida",
    47158: "Insecta",
    47126: "Plantae",
    47170: "Fungi",
    48222: "Chromista",
    47686: "Protozoa",
}

# Taxonomic ranks that can be filtered on
RANKS = [
    "form",
    "variety",
    "subspecies",
    "hybrid",
    "species",
    "genushybrid",
    "subgenus",
    "genus",
    "subtribe",
    "tribe",
    "supertribe",
    "subfamily",
    "family",
    "epifamily",
    "superfamily",
    "infraorder",
    "suborder",
    "order",
    "superorder",
    "infraclass",
    "subclass",
    "class",
    "superclass",
    "subphylum",
    "phylum",
    "kingdom",
]

# Endpoint-specific options for multiple choice parameters
NODE_OBS_ORDER_BY_PROPERTIES = ["created_at", "id", "observed_on", "species_guess", "votes"]
REST_OBS_ORDER_BY_PROPERTIES = ["date_added", "observed_on"]
PROJECT_ORDER_BY_PROPERTIES = ["created", "distance", "featured", "recent_posts", "updated"]

# Options for multiple choice parameters (non-endpoint-specific)
COMMUNITY_ID_STATUSES = ["most_agree", "most_disagree", "some_agree"]
EXTRA_PROPERTIES = ["fields", "identifications", "projects"]
GEOPRIVACY_LEVELS = ["obscured", "obscured_private", "open", "private"]
HAS_PROPERTIES = ["photo", "geo"]
ORDER_DIRECTIONS = ["asc", "desc"]
PROJECT_TYPES = ["collection", "umbrella"]
QUALITY_GRADES = ["casual", "needs_id", "research"]
SEARCH_PROPERTIES = ["names", "tags", "description", "place"]


# Multiple-choice request parameters, with keys mapped to their possible choices (non-endpoint-specific)
MULTIPLE_CHOICE_PARAMS = {
    "csi": CONSERVATION_STATUSES,
    "extra": EXTRA_PROPERTIES,
    "geoprivacy": GEOPRIVACY_LEVELS,
    "has": HAS_PROPERTIES,
    "hrank": RANKS,
    "iconic_taxa": list(ICONIC_TAXA.values()),
    "identifications": COMMUNITY_ID_STATUSES,
    "license": CC_LICENSES,
    "lrank": RANKS,
    "max_rank": RANKS,
    "min_rank": RANKS,
    "order": ORDER_DIRECTIONS,
    "photo_license": CC_LICENSES,
    "quality_grade": QUALITY_GRADES,
    "rank": RANKS,
    "search_on": SEARCH_PROPERTIES,
    "sound_license": CC_LICENSES,
    "taxon_geoprivacy": GEOPRIVACY_LEVELS,
    "type": PROJECT_TYPES,
}

MULTIPLE_CHOICE_ERROR_MSG = (
    "Parameter '{}' must have one of the following values: {}\n\tValue provided: {}"
)

logger = getLogger(__name__)


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


def convert_bool_params(params: RequestParams) -> RequestParams:
    """ Convert any boolean request parameters to javascript-style boolean strings """
    for k, v in params.items():
        if isinstance(v, bool):
            params[k] = str(v).lower()
    return params


def convert_datetime_params(params: RequestParams) -> RequestParams:
    """Convert any dates, datetimes, or timestamps in other formats into ISO 8601 strings.

    API behavior note: params that take date but not time info will accept a full timestamp and
    just ignore the time, so it's safe to parse both date and datetime strings into timestamps

    Raises:
        :py:exc:`dateutil.parser._parser.ParserError` if a date/datetime format is invalid
    """
    for k, v in params.items():
        if isinstance(v, datetime) or isinstance(v, date):
            params[k] = _isoformat(v)
        if v is not None and k in DATETIME_PARAMS:
            params[k] = _isoformat(parse_timestamp(v))

    return params


def ensure_file_obj(photo: FileOrPath) -> BinaryIO:
    """Given a file objects or path, read it into a file-like object if it's a path"""
    if isinstance(photo, str):
        file_path = abspath(expanduser(photo))
        logger.info(f"Reading from file: {file_path}")
        with open(file_path, "rb") as f:
            return BytesIO(f.read())
    return photo


def ensure_file_objs(photos: Iterable[FileOrPath]) -> Iterable[BinaryIO]:
    """Given one or more file objects and/or paths, read any paths into a file-like object"""
    return [ensure_file_obj(photo) for photo in ensure_list(photos)]


def ensure_list(values: Any):
    """If the value is a string or comma-separated list of values, convert it into a list"""
    if not values:
        values = []
    elif isinstance(values, str) and "," in values:
        values = values.split(",")
    elif not isinstance(values, list):
        values = [values]
    return values


def convert_list(obj: Any) -> str:
    """Convert list parameters into an API-compatible (comma-delimited) string"""
    if not obj:
        return ""
    if isinstance(obj, list):
        return ",".join(map(str, obj))
    return str(obj)


def convert_list_params(params: RequestParams) -> RequestParams:
    """Convert any list parameters into an API-compatible (comma-delimited) string.
    Will be url-encoded by requests. For example: `['k1', 'k2', 'k3'] -> k1%2Ck2%2Ck3`
    """
    return {k: convert_list(v) for k, v in params.items()}


def convert_observation_fields(params: RequestParams) -> RequestParams:
    """Translate simplified format of observation field values into API-compatible format"""
    if "observation_fields" in params:
        params["observation_field_values_attributes"] = params.pop("observation_fields")
    obs_fields = params.get("observation_field_values_attributes")
    if isinstance(obs_fields, dict):
        params["observation_field_values_attributes"] = [
            {"observation_field_id": k, "value": v} for k, v in obs_fields.items()
        ]
    return params


def strip_empty_params(params: RequestParams) -> RequestParams:
    """Remove any request parameters with empty or ``None`` values."""
    return {k: v for k, v in params.items() if v or v is False}


def is_int(value: Any) -> bool:
    """ Determine if a value is a valid integer """
    try:
        int(value)
        return True
    except (TypeError, ValueError):
        return False


def is_int_list(values: Any) -> bool:
    """Determine if a value contains one or more valid integers"""
    return all([is_int(v) for v in ensure_list(values)])


def validate_ids(ids: Any) -> str:
    """Ensure ID(s) are all valid integers, and convert to a comma-delimited string if multiple

    Raises:
        :py:exc:`ValueError` if any values are not valid integers
    """
    if not is_int_list(ids):
        raise ValueError(f"Invalid ID(s): {ids}; must specify integers only")
    return convert_list([int(id) for id in ensure_list(ids)])


def is_valid_multiple_choice_option(value: Any, choices: Iterable) -> bool:
    """Determine if a multiple-choice request parameter contains valid value(s)."""
    if not value:
        return True
    if not isinstance(value, list):
        value = [value]
    return all([v in choices for v in value])


def validate_multiple_choice_param(params: RequestParams, key: str, choices: Iterable):
    """Verify if a multiple-choice request parameter contains valid value(s);
    if not, raise an error. **Used for endpoint-specific params.**

    Raises:
        :py:exc:`ValueError`
    """
    if key in params and not is_valid_multiple_choice_option(params[key], choices):
        raise ValueError(MULTIPLE_CHOICE_ERROR_MSG.format(key, choices, params[key]))


def validate_multiple_choice_params(params: RequestParams):
    """Verify that multiple-choice request parameters contain a valid value.

    **Note:** This does not check endpoint-specific params, i.e., those that have the same name
    but different values across different endpoints.

    Raises:
        :py:exc:`ValueError`;
            Error message will contain info on all validation errors, if there are multiple
    """
    # Collect info on any validation errors
    errors = []
    for key, choices in MULTIPLE_CHOICE_PARAMS.items():
        if key in params and not is_valid_multiple_choice_option(params[key], choices):
            errors.append(MULTIPLE_CHOICE_ERROR_MSG.format(key, choices, params[key]))

    # Combine all messages (if multiple) into one error message
    if errors:
        raise ValueError("\n".join(errors))


def _isoformat(d):
    """Return a date or datetime in ISO format.
    If it's a datetime and doesn't already have tzinfo, set it to the system's local timezone.
    """
    if isinstance(d, datetime) and not d.tzinfo:
        d = d.replace(tzinfo=tzlocal())
    return d.isoformat()


def translate_rank_range(params: RequestParams) -> RequestParams:
    """If min and/or max rank is specified in params, translate into a list of ranks"""

    def _get_rank_index(rank: str) -> int:
        if rank not in RANKS:
            raise ValueError("Invalid rank")
        return RANKS.index(rank)

    min_rank, max_rank = params.pop("min_rank", None), params.pop("max_rank", None)
    if min_rank or max_rank:
        # Use indices in RANKS list to determine range of ranks to include
        min_rank_index = _get_rank_index(min_rank) if min_rank else 0
        max_rank_index = _get_rank_index(max_rank) + 1 if max_rank else len(RANKS)
        params["rank"] = RANKS[min_rank_index:max_rank_index]
    return params


def warn(msg):
    warnings.warn(DeprecationWarning(msg))
