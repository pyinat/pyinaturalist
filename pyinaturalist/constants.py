from datetime import date, datetime
from typing import Any, BinaryIO, Dict, List, Union

INAT_NODE_API_BASE_URL = "https://api.inaturalist.org/v1/"
INAT_BASE_URL = "https://www.inaturalist.org"
INAT_KEYRING_KEY = "/inaturalist"

PER_PAGE_RESULTS = 30  # Number of records per page for paginated queries
THROTTLING_DELAY = 1  # In seconds, support <1 floats such as 0.1

# Toggle dry-run mode: this will run and log mock HTTP requests instead of real ones
DRY_RUN_ENABLED = False  # Mock all requests, including GET
DRY_RUN_WRITE_ONLY = False  # Only mock 'write' requests
WRITE_HTTP_METHODS = ["PATCH", "POST", "PUT", "DELETE"]

# Type aliases
Date = Union[date, datetime, str]
DateTime = Union[date, datetime, str]
FileOrPath = Union[BinaryIO, str]
IntOrStr = Union[int, str]
JsonResponse = Dict[str, Any]
ListResponse = List[Dict[str, Any]]
ObsFieldValues = Union[Dict, List[Dict]]
RequestParams = Dict[str, Any]
MultiInt = Union[int, List[int]]
MultiStr = Union[str, List[str]]
TemplateFunction = Any  # Cannot use Callable/Protocol, as they will not allow a mix of signatures
