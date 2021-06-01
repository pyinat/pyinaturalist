from datetime import date, datetime
from os.path import abspath, dirname, join
from pathlib import Path
from typing import IO, Any, BinaryIO, Dict, Iterable, List, Tuple, Union

# iNaturalist URLs
API_V0_BASE_URL = 'https://www.inaturalist.org'
API_V1_BASE_URL = 'https://api.inaturalist.org/v1'
API_V2_BASE_URL = 'https://api.inaturalist.org/v2'
DWC_ARCHIVE_URL = 'http://www.inaturalist.org/observations/gbif-observations-dwca.zip'
EXPORT_URL = 'https://www.inaturalist.org/observations/export'
PHOTO_BASE_URL = 'https://static.inaturalist.org/photos'
PHOTO_INFO_BASE_URL = 'https://www.inaturalist.org/photos'

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

# Relevant project directories
PROJECT_DIR = abspath(dirname(dirname(__file__)))
DOWNLOAD_DIR = join(PROJECT_DIR, 'downloads')
SAMPLE_DATA_DIR = join(PROJECT_DIR, 'test', 'sample_data')

# Type aliases
Coordinates = Tuple[float, float]
AnyDate = Union[date, datetime, str]
AnyDateTime = Union[datetime, str]
AnyFile = Union[IO, Path, str]
DateOrInt = Union[date, datetime, int]
Dimensions = Tuple[int, int]
FileOrPath = Union[BinaryIO, str]
HistogramResponse = Dict[DateOrInt, int]
IntOrStr = Union[int, str]
JsonResponse = Dict[str, Any]
ListResponse = List[Dict[str, Any]]
ObsFieldValues = Union[Dict, List[Dict]]
RequestParams = Dict[str, Any]
ResponseObject = Dict[str, Any]
ResponseOrObject = Union[JsonResponse, ResponseObject, Iterable[ResponseObject]]
ResponseOrFile = Union[AnyFile, JsonResponse]
MultiFile = Union[FileOrPath, Iterable[FileOrPath]]
MultiInt = Union[int, Iterable[int]]
MultiStr = Union[str, Iterable[str]]
MultiIntOrStr = Union[MultiInt, MultiStr]
TemplateFunction = Any  # Cannot use Callable/Protocol, as these will not allow a mix of signatures
