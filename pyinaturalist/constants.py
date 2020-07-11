from datetime import date, datetime
from typing import Any, Dict, List, Union

INAT_NODE_API_BASE_URL = "https://api.inaturalist.org/v1/"
INAT_BASE_URL = "https://www.inaturalist.org"

PER_PAGE_RESULTS = 30  # Number of records per page for paginated queries
THROTTLING_DELAY = 1  # In seconds, support <1 floats such as 0.1

# Toggle dry-run mode: this will run and log mock HTTP requests instead of real ones
DRY_RUN_ENABLED = False  # Mock all requests, including GET
DRY_RUN_WRITE_ONLY = False  # Only mock 'write' requests
WRITE_HTTP_METHODS = ["PATCH", "POST", "PUT", "DELETE"]

# Type aliases
Date = Union[date, datetime, str]
DateTime = Union[date, datetime, str]
IntOrStr = Union[int, str]
JsonResponse = Dict[str, Any]
MultiInt = Union[int, List[int]]
MultiStr = Union[str, List[str]]

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

# Main taxa "categories" that can be filtered on
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

# Additional options for multiple-choice search filters, used for validation
COMMUNITY_ID_STATUSES = ["most_agree", "most_disagree", "some_agree"]
GEOPRIVACY_LEVELS = ["obscured", "obscured_private", "open", "private"]
ORDER_DIRECTIONS = ["asc", "desc"]
ORDER_BY_PROPERTIES = ["created_at", "id", "observed_on", "species_guess", "votes"]
SEARCH_PROPERTIES = ["names", "tags", "description", "place"]
QUALITY_GRADES = ["casual", "needs_id", "research"]
