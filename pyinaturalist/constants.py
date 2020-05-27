import requests
from unittest.mock import Mock

INAT_NODE_API_BASE_URL = "https://api.inaturalist.org/v1/"
INAT_BASE_URL = "https://www.inaturalist.org"

THROTTLING_DELAY = 1  # In seconds, support <1 floats such as 0.1

# Toggle dry-run mode: this will run and log mock HTTP requests instead of real ones
DRY_RUN_ENABLED = False
# Mock response content to return in dry-run mode
MOCK_RESPONSE = Mock(spec=requests.Response)
MOCK_RESPONSE.json.return_value = {"results": ["nodata"]}

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


# Taxonomic ranks from Node API Swagger spec
RANKS = [
    "form",
    "variety",
    "subspecies",
    "hybrid",
    "species",
    "genushybrid",
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
    "subclass",
    "class",
    "superclass",
    "subphylum",
    "phylum",
    "kingdom",
]
