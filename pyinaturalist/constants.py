# ruff: noqa: F401
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from os.path import abspath, dirname, join
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, BinaryIO, Dict, Iterable, List, Optional, Tuple, Union

from dateutil.relativedelta import relativedelta
from platformdirs import user_data_dir
from pyrate_limiter.sqlite_bucket import LOCK_PATH as DEFAULT_LOCK_PATH


# iNaturalist URLs
API_V0 = 'https://www.inaturalist.org'
API_V1 = 'https://api.inaturalist.org/v1'
API_V2 = 'https://api.inaturalist.org/v2'
EXPORT_URL = 'https://www.inaturalist.org/observations/export'
GBIF_TAXON_BASE_URL = 'https://www.gbif.org/species'
INAT_BASE_URL = API_V0
INAT_REPO = 'https://raw.githubusercontent.com/inaturalist/inaturalist/main'
ICONIC_TAXA_BASE_URL = f'{INAT_REPO}/app/assets/images/iconic_taxa'
PHOTO_BASE_URL = 'https://static.inaturalist.org/photos'
PHOTO_CC_BASE_URL = 'https://inaturalist-open-data.s3.amazonaws.com/photos'
PHOTO_INFO_BASE_URL = 'https://www.inaturalist.org/photos'

# Prefix used for keyring entries
KEYRING_KEY = '/inaturalist'

# Pagination settings
PER_PAGE_RESULTS = 200  # Default number of records per page for paginated queries
LARGE_REQUEST_WARNING = 5000  # Show a warning for queries that will return over this many results

# Rate-limiting and retry settings
CONNECT_TIMEOUT = 5
MAX_DELAY = 60  # Maximum time to wait for rate-limiting before aborting
REQUEST_BURST_RATE = 5
REQUESTS_PER_SECOND = 1
REQUESTS_PER_MINUTE = 60
REQUESTS_PER_DAY = 10000
REQUEST_TIMEOUT = 20
REQUEST_RETRIES = 5  # Maximum number of retries for a failed request
RETRY_BACKOFF = 0.5  # Exponential backoff factor for retries
RETRY_STATUSES = (500, 502, 503, 504)

# HTTP methods that apply to write-only dry-run mode
WRITE_HTTP_METHODS = ['PATCH', 'POST', 'PUT', 'DELETE']

# Project directories
PROJECT_DIR = abspath(dirname(dirname(__file__)))
DATA_DIR = Path(user_data_dir()) / 'pyinaturalist'
DOCS_DIR = join(PROJECT_DIR, 'docs')
DOWNLOAD_DIR = join(PROJECT_DIR, 'downloads')
EXAMPLES_DIR = join(PROJECT_DIR, 'examples')
SAMPLE_DATA_DIR = join(PROJECT_DIR, 'test', 'sample_data')

# Cache settings
CACHE_EXPIRATION = {
    'api.inaturalist.org/*autocomplete': timedelta(days=30),
    'api.inaturalist.org/v*/controlled_terms*': timedelta(days=7),
    'api.inaturalist.org/v*/places*': timedelta(days=7),
    'api.inaturalist.org/v*/taxa*': timedelta(days=7),
    'www.inaturalist.org/users/api_token': timedelta(days=1),
    f'{PHOTO_CC_BASE_URL}/*': -1,
    f'{PHOTO_BASE_URL}/*': -1,
    f'{ICONIC_TAXA_BASE_URL}/*': -1,
    '*': timedelta(minutes=30),
}
CACHE_FILE = join(DATA_DIR, 'api_requests.db')
RATELIMIT_FILE = join(DATA_DIR, 'api_ratelimit.db')

# Response formats supported by v0 GET /observations endpoint
OBSERVATION_FORMATS = ['atom', 'csv', 'dwc', 'json', 'kml', 'widget']

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

COLORS = {
    'blue': '#5778a4',
    'orange': '#e49444',
    'red': '#d1615d',
    'teal': '#85b6b2',
    'green': '#6a9f58',
    'yellow': '#e7ca60',
    'purple': '#a87c9f',
    'pink': '#f1a2a9',
    'brown': '#967662',
    'grey': '#b8b0ac',
    'black': '#000000',
}


@dataclass
class FontAwesomeIcon:
    prefix: str
    name: str
    color: str
    size: int = 16

    def __str__(self):
        return (
            f'<i class="{self.prefix} {self.name}"'
            f'style="color: {COLORS[self.color]};'
            f'font-size: {self.size}px;"></i>'
        )

    def __repr__(self):
        return f'<FontAwesomeIcon {self.prefix} {self.name} {self.color} {self.size}>'


ICONIC_FONT_AWESOME = {
    0: FontAwesomeIcon('fa-solid', 'fa-question-circle', 'grey'),
    1: FontAwesomeIcon('fa-solid', 'fa-paw', 'black'),
    3: FontAwesomeIcon('fa-solid', 'fa-dove', 'teal'),
    20978: FontAwesomeIcon('fa-solid', 'fa-frog', 'green'),
    26036: FontAwesomeIcon('fa-solid', 'fa-dragon', 'green'),
    40151: FontAwesomeIcon('fa-solid', 'fa-cat', 'orange'),
    47178: FontAwesomeIcon('fa-solid', 'fa-fish', 'blue'),
    47115: FontAwesomeIcon('fa-solid', 'fa-worm', 'pink'),
    47119: FontAwesomeIcon('fa-solid', 'fa-spider', 'black'),
    47158: FontAwesomeIcon('fa-solid', 'fa-mosquito', 'purple'),
    47126: FontAwesomeIcon('fa-solid', 'fa-leaf', 'green'),
    47170: FontAwesomeIcon('fa-solid', 'fa-bacteria', 'brown'),  # mushroom
    48222: FontAwesomeIcon('fa-solid', 'fa-bowling-ball', 'green'),
    47686: FontAwesomeIcon('fa-solid', 'fa-disease', 'green'),
}

assert set(ICONIC_TAXA.keys()) == set(ICONIC_EMOJI.keys())
assert set(ICONIC_TAXA.keys()) == set(ICONIC_FONT_AWESOME.keys())

ROOT_TAXON_ID = 48460

# Taxonomic ranks that can be filtered on, and numeric values for comparison
# Source: https://github.com/inaturalist/inaturalist/blob/main/app/models/taxon.rb
UNRANKED = 90  # Used for comparing unranked taxa
RANK_LEVELS = {
    'infrahybrid': 5,
    'form': 5,
    'variety': 5,
    'subspecies': 5,
    'hybrid': 10,
    'species': 10,
    'complex': 11,
    'subsection': 12,
    'section': 13,
    'subgenus': 15,
    'genushybrid': 20,
    'genus': 20,
    'subtribe': 24,
    'tribe': 25,
    'supertribe': 26,
    'subfamily': 27,
    'family': 30,
    'epifamily': 32,
    'superfamily': 33,
    'zoosubsection': 33.5,
    'zoosection': 34,
    'parvorder': 34.5,
    'infraorder': 35,
    'suborder': 37,
    'order': 40,
    'superorder': 43,
    'subterclass': 44,
    'infraclass': 45,
    'subclass': 47,
    'class': 50,
    'superclass': 53,
    'subphylum': 57,
    'phylum': 60,
    'kingdom': 70,
    'unranked': UNRANKED,
    'stateofmatter': 100,
}
RANKS = list(RANK_LEVELS.keys())[:-2]

# The main 7 taxonomic ranks, used for condensed display
COMMON_RANKS = [
    'species',
    'genus',
    'family',
    'order',
    'class',
    'phylum',
    'kingdom',
]

# Additional equivalents that iNat accepts; see request_params.normalize_rank() for more variations
RANK_EQUIVALENTS = {
    'division': 'phylum',
    'gen': 'genus',
    'sp': 'species',
    'spp': 'species',
    'infraspecies': 'subspecies',
    'ssp': 'subspecies',
    'subsp': 'subspecies',
    'trinomial': 'subspecies',
    'var': 'variety',
}


# Options for multiple choice parameters (non-endpoint-specific)
CC_LICENSES = ['CC-BY', 'CC-BY-NC', 'CC-BY-ND', 'CC-BY-SA', 'CC-BY-NC-ND', 'CC-BY-NC-SA', 'CC0']
ALL_LICENSES = CC_LICENSES + ['ALL RIGHTS RESERVED']
COMMUNITY_ID_STATUSES = ['most_agree', 'most_disagree', 'some_agree']
CONSERVATION_STATUSES = ['LC', 'NT', 'VU', 'EN', 'CR', 'EW', 'EX']
ESTABLISTMENT_MEANS = ['introduced', 'native', 'endemic']
EXTRA_PROPERTIES = ['fields', 'identifications', 'projects']
GEOPRIVACY_LEVELS = ['obscured', 'obscured_private', 'open', 'private']
HAS_PROPERTIES = ['photo', 'geo']
HISTOGRAM_DATE_FIELDS = ['created', 'observed']
HISTOGRAM_INTERVALS = ['year', 'month', 'week', 'day', 'hour', 'month_of_year', 'week_of_year']
ICON_SIZES = {'icon': 32, 'square': 75, 'small': 75, 'medium': 200, 'large': 200, 'original': 200}
ID_CATEGORIES = ['improving', 'supporting', 'leading', 'maverick']
INBOXES = ['inbox', 'sent', 'any']
ORDER_DIRECTIONS = ['asc', 'desc']
PHOTO_SIZES = ['square', 'small', 'medium', 'large', 'original']
PLACE_CATEGORIES = ['standard', 'community']
PROJECT_TYPES = ['assessment', 'bioblitz', 'collection', 'umbrella']
QUALITY_GRADES = ['casual', 'needs_id', 'research']
SEARCH_PROPERTIES = ['names', 'tags', 'description', 'place']
SOURCES = ['places', 'projects', 'taxa', 'users']

# Endpoint-specific options for multiple choice parameters
V0_OBS_ORDER_BY_PROPERTIES = ['date_added', 'observed_on']
V1_OBS_ORDER_BY_PROPERTIES = ['created_at', 'id', 'observed_on', 'species_guess', 'votes']
V2_OBS_ORDER_BY_PROPERTIES = [
    'created_at',
    'id',
    'observed_on',
    'species_guess',
    'updated_at',
    'votes',
    'random',
]
PROJECT_ORDER_BY_PROPERTIES = ['created', 'distance', 'featured', 'recent_posts', 'updated']

# Multiple-choice request parameters, with keys mapped to their possible choices (non-endpoint-specific)
# TODO: python 3.11 supports Literal[*list] syntax, which would be useful here
MULTIPLE_CHOICE_PARAMS = {
    'box': INBOXES,
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

# Request parameters from all API versions that accept date or datetime strings
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
    'prefers_rule_d1',
    'prefers_rule_d2',
    'since',
    'updated_since',
]
DATETIME_SHORT_FORMAT = '%b %d, %Y'

# Type aliases
Coordinates = Tuple[float, float]
AnyDate = Union[date, datetime, str]
AnyDateTime = Union[datetime, str]
AnyFile = Union[IO, Path, str]
DateTime = datetime
DateOrInt = Union[date, datetime, int]
DateOrStr = Union[date, datetime, str]
DateOrDatetime = Union[date, datetime]
DateRange = Tuple[DateOrDatetime, DateOrDatetime]
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
TimeInterval = Union[str, timedelta, relativedelta]

# For type checking purposes, some nullable attrs need to be marked as Optional.
# For documentation purposes, this is redundant since all keyword args are optional.
if TYPE_CHECKING:
    Coordinates = Optional[Coordinates]  # type: ignore
    DateTime = Optional[DateTime]  # type: ignore
