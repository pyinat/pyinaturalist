from datetime import date, datetime
from os.path import abspath, dirname, join
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, BinaryIO, Dict, Iterable, List, Optional, Tuple, Union

# iNaturalist URLs
API_V0_BASE_URL = 'https://www.inaturalist.org'
API_V1_BASE_URL = 'https://api.inaturalist.org/v1'
API_V2_BASE_URL = 'https://api.inaturalist.org/v2'
DWC_ARCHIVE_URL = 'http://www.inaturalist.org/observations/gbif-observations-dwca.zip'
EXPORT_URL = 'https://www.inaturalist.org/observations/export'
INAT_BASE_URL = API_V0_BASE_URL
INAT_REPO = 'https://raw.githubusercontent.com/inaturalist/inaturalist/main'
ICONIC_TAXA_BASE_URL = f'{INAT_REPO}/app/assets/images/iconic_taxa'
PHOTO_BASE_URL = 'https://static.inaturalist.org/photos'
PHOTO_INFO_BASE_URL = 'https://www.inaturalist.org/photos'

# Prefix used for keyring entries
KEYRING_KEY = '/inaturalist'

# Pagination and rate-limiting values
PER_PAGE_RESULTS = 200  # Default number of records per page for paginated queries
THROTTLING_DELAY = 1.0  # Delay between paginated queries, in seconds
MAX_DELAY = 60  # Maximum time to wait for rate-limiting before aborting
REQUESTS_PER_SECOND = 2
REQUESTS_PER_MINUTE = 60
REQUESTS_PER_DAY = 10000
LARGE_REQUEST_WARNING = 5000  # Show a warning for queries that will return over this many results

PHOTO_SIZES = ['square', 'small', 'medium', 'large', 'original']

# Toggle dry-run mode: this will run and log mock HTTP requests instead of real ones
DRY_RUN_ENABLED = False  # Mock all requests, including GET
DRY_RUN_WRITE_ONLY = False  # Only mock 'write' requests
WRITE_HTTP_METHODS = ['PATCH', 'POST', 'PUT', 'DELETE']

# Project directories
PROJECT_DIR = abspath(dirname(dirname(__file__)))
DOCS_DIR = join(PROJECT_DIR, 'docs')
DOWNLOAD_DIR = join(PROJECT_DIR, 'downloads')
SAMPLE_DATA_DIR = join(PROJECT_DIR, 'test', 'sample_data')

# Response formats supported by GET /observations endpoint
OBSERVATION_FORMATS = ['atom', 'csv', 'dwc', 'json', 'kml', 'widget']

# IUCN Conservation status codes; for more info, see: https://www.iucnredlist.org
CONSERVATION_STATUSES = ['LC', 'NT', 'VU', 'EN', 'CR', 'EW', 'EX', 'S2B']

# Taxon ID and name of main taxa 'categories' that can be filtered on
ICONIC_TAXA = {
    0: 'Unknown',
    1: 'Animalia',
    3: 'Aves',
    20978: 'Amphibia',
    26036: 'Reptilia',
    40151: 'Mammalia',
    47178: 'Actinopterygii',
    47115: 'Mollusca',
    47119: 'Arachnida',
    47158: 'Insecta',
    47126: 'Plantae',
    47170: 'Fungi',
    48222: 'Chromista',
    47686: 'Protozoa',
}
# TODO: More emoji for non-iconic taxa?
ICONIC_EMOJI = {
    0: '❓',
    1: '🐾',
    3: '🐦',
    20978: '🐸',
    26036: '🦎',
    40151: '😺',
    47178: '🐠',
    47115: '🐌',
    47119: '🕷️',
    47158: '🦋',
    47126: '🌿',
    47170: '🍄',
    48222: '🟢',
    47686: '🦠',
}

# Taxonomic ranks that can be filtered on
RANKS = [
    'form',
    'variety',
    'subspecies',
    'hybrid',
    'species',
    'genushybrid',
    'subgenus',
    'genus',
    'subtribe',
    'tribe',
    'supertribe',
    'subfamily',
    'family',
    'epifamily',
    'superfamily',
    'infraorder',
    'suborder',
    'order',
    'superorder',
    'infraclass',
    'subclass',
    'class',
    'superclass',
    'subphylum',
    'phylum',
    'kingdom',
]

# Endpoint-specific options for multiple choice parameters
NODE_OBS_ORDER_BY_PROPERTIES = ['created_at', 'id', 'observed_on', 'species_guess', 'votes']
REST_OBS_ORDER_BY_PROPERTIES = ['date_added', 'observed_on']
PROJECT_ORDER_BY_PROPERTIES = ['created', 'distance', 'featured', 'recent_posts', 'updated']

# Options for multiple choice parameters (non-endpoint-specific)
CC_LICENSES = ['CC-BY', 'CC-BY-NC', 'CC-BY-ND', 'CC-BY-SA', 'CC-BY-NC-ND', 'CC-BY-NC-SA', 'CC0']
ALL_LICENSES = CC_LICENSES + ['ALL RIGHTS RESERVED']
COMMUNITY_ID_STATUSES = ['most_agree', 'most_disagree', 'some_agree']
ESTABLISTMENT_MEANS = ['introduced', 'native', 'endemic']
EXTRA_PROPERTIES = ['fields', 'identifications', 'projects']
GEOPRIVACY_LEVELS = ['obscured', 'obscured_private', 'open', 'private']
HAS_PROPERTIES = ['photo', 'geo']
HISTOGRAM_DATE_FIELDS = ['created', 'observed']
HISTOGRAM_INTERVALS = ['year', 'month', 'week', 'day', 'hour', 'month_of_year', 'week_of_year']
ID_CATEGORIES = ['improving', 'supporting', 'leading', 'maverick']
ORDER_DIRECTIONS = ['asc', 'desc']
PLACE_CATEGORIES = ['standard', 'community']
PROJECT_TYPES = ['collection', 'umbrella']
QUALITY_GRADES = ['casual', 'needs_id', 'research']
SEARCH_PROPERTIES = ['names', 'tags', 'description', 'place']
SOURCES = ['places', 'projects', 'taxa', 'users']

# Multiple-choice request parameters, with keys mapped to their possible choices (non-endpoint-specific)
MULTIPLE_CHOICE_PARAMS = {
    'category': ID_CATEGORIES,
    'csi': CONSERVATION_STATUSES,
    'date_field': HISTOGRAM_DATE_FIELDS,
    'extra': EXTRA_PROPERTIES,
    'geoprivacy': GEOPRIVACY_LEVELS,
    'has': HAS_PROPERTIES,
    'hrank': RANKS,
    'iconic_taxa': list(ICONIC_TAXA.values()),
    'identifications': COMMUNITY_ID_STATUSES,
    'interval': HISTOGRAM_INTERVALS,
    'license': CC_LICENSES,
    'lrank': RANKS,
    'max_rank': RANKS,
    'min_rank': RANKS,
    'observation_hrank': RANKS,
    'observation_lrank': RANKS,
    'observation_rank': RANKS,
    'order': ORDER_DIRECTIONS,
    'photo_license': CC_LICENSES,
    'quality_grade': QUALITY_GRADES,
    'rank': RANKS,
    'search_on': SEARCH_PROPERTIES,
    'sound_license': CC_LICENSES,
    'sources': SOURCES,
    'taxon_geoprivacy': GEOPRIVACY_LEVELS,
    'type': PROJECT_TYPES,
}

# All request parameters from both Node API and REST (Rails) API that accept date or datetime strings
DATETIME_PARAMS = [
    'created_after',
    'created_d1',
    'created_d2',
    'created_on',
    'd1',
    'd2',
    'newer_than',
    'observation_created_d1',
    'observation_created_d2',
    'observed_d1',
    'observed_d2',
    'observed_on',
    'observed_on_string',
    'older_than',
    'on',
    'since',
    'updated_since',  # TODO: test if this one behaves differently in Node API vs REST API
]

# Type aliases
Coordinates = Tuple[float, float]
AnyDate = Union[date, datetime, str]
AnyDateTime = Union[datetime, str]
AnyFile = Union[IO, Path, str]
DateTime = datetime
DateOrInt = Union[date, datetime, int]
Dimensions = Tuple[int, int]
FileOrPath = Union[BinaryIO, str]
GeoJson = Dict[str, Any]
HistogramResponse = Dict[DateOrInt, int]
IntOrStr = Union[int, str]
JsonResponse = Dict[str, Any]
ListResponse = List[Dict[str, Any]]
ObsFieldValues = Union[Dict, List[Dict]]
RequestParams = Dict[str, Any]
ResponseResult = Dict[str, Any]
ResponseOrResults = Union[JsonResponse, Iterable[ResponseResult]]
ResponseOrFile = Union[AnyFile, JsonResponse]
MultiFile = Union[FileOrPath, Iterable[FileOrPath]]
MultiInt = Union[int, Iterable[int]]
MultiStr = Union[str, Iterable[str]]
MultiIntOrStr = Union[MultiInt, MultiStr]
TableRow = Dict[str, Any]
TemplateFunction = Any  # Cannot use Callable/Protocol, as these will not allow a mix of signatures

# For type checking purposes, some nullable attrs need to be marked as Optional.
# For documentation purposes, this is redundant since all keyword args are optional.
if TYPE_CHECKING:
    Coordinates = Optional[Coordinates]  # type: ignore
    DateTime = Optional[DateTime]  # type: ignore
