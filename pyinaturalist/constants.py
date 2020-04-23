INAT_NODE_API_BASE_URL = "https://api.inaturalist.org/v1/"
INAT_BASE_URL = "https://www.inaturalist.org"

THROTTLING_DELAY = 1  # In seconds, support <0 floats such as 0.1

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
