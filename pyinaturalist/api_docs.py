"""
Reusable template functions used for API documentation.
Each template function contains a portion of an endpoint's request parameters, with corresponding
type annotations and docstrings.
"""
from typing import List, Iterable

from pyinaturalist.constants import (
    MultiInt,
    MultiStr,
    Date,
    DateTime,
    IntOrStr,
    FileOrPath,
    ObsFieldValues,
)
from pyinaturalist.request_params import MULTIPLE_CHOICE_PARAMS


# Observations
# --------------------


# Params that are in most observation-related endpoints in both Node and REST APIs
def _observation_common(
    q: str = None,
    d1: Date = None,
    d2: Date = None,
    day: MultiInt = None,
    month: MultiInt = None,
    year: MultiInt = None,
    license: MultiStr = None,
    list_id: int = None,
    photo_license: MultiStr = None,
    out_of_range: bool = None,
    quality_grade: str = None,
    taxon_id: MultiInt = None,
    taxon_name: MultiStr = None,
    iconic_taxa: MultiStr = None,
    updated_since: DateTime = None,
):
    """
    q: Search observation properties
    d1: Must be observed on or after this date
    d2: Must be observed on or before this date
    day: Must be observed within this day of the month
    month: Must be observed within this month
    year: Must be observed within this year
    license: Observation must have this license
    photo_license: Must have at least one photo with this license
    out_of_range: Observations whose taxa are outside their known ranges
    list_id: Taxon must be in the list with this ID
    quality_grade: Must have this quality grade
    taxon_id: Only show observations of these taxa and their descendants
    taxon_name: Taxon must have a scientific or common name matching this string
    iconic_taxa: Taxon must by within this iconic taxon
    updated_since: Must be updated since this time
    """


# Observation params that are only in the Node API
def _observation_node_only(
    acc: bool = None,
    captive: bool = None,
    endemic: bool = None,
    geo: bool = None,
    id_please: bool = None,
    identified: bool = None,
    introduced: bool = None,
    mappable: bool = None,
    native: bool = None,
    pcid: bool = None,
    photos: bool = None,
    popular: bool = None,
    sounds: bool = None,
    taxon_is_active: bool = None,
    threatened: bool = None,
    verifiable: bool = None,
    id: MultiInt = None,
    not_id: MultiInt = None,
    sound_license: MultiStr = None,
    ofv_datatype: MultiStr = None,
    place_id: MultiInt = None,
    project_id: MultiInt = None,
    rank: MultiStr = None,
    site_id: MultiStr = None,
    without_taxon_id: MultiInt = None,
    user_id: MultiInt = None,
    user_login: MultiStr = None,
    term_id: MultiInt = None,
    term_value_id: MultiInt = None,
    without_term_value_id: MultiInt = None,
    acc_above: str = None,
    acc_below: str = None,
    created_d1: DateTime = None,
    created_d2: DateTime = None,
    created_on: Date = None,
    observed_on: Date = None,
    unobserved_by_user_id: int = None,
    apply_project_rules_for: str = None,
    cs: str = None,
    csa: str = None,
    csi: MultiStr = None,
    geoprivacy: MultiStr = None,
    taxon_geoprivacy: MultiStr = None,
    max_rank: str = None,
    min_rank: str = None,
    hrank: str = None,
    lrank: str = None,
    id_above: int = None,
    id_below: int = None,
    identifications: str = None,
    lat: float = None,
    lng: float = None,
    radius: float = None,
    not_in_project: IntOrStr = None,
    not_matching_project_rules_for: IntOrStr = None,
    search_on: str = None,
    viewer_id: int = None,
    reviewed: bool = None,
    locale: str = None,
    preferred_place_id: int = None,
    ttl: str = None,
):
    """
    acc: Whether or not positional accuracy / coordinate uncertainty has been specified
    captive: Captive or cultivated observations
    endemic: Observations whose taxa are endemic to their location
    geo: Observations that are georeferenced
    id_please: Observations with the **deprecated** "ID, Please!" flag.
        Note that this will return observations, but that this attribute is no longer used.
    identified: Observations that have community identifications
    introduced: Observations whose taxa are introduced in their location
    mappable: Observations that show on map tiles
    native: Observations whose taxa are native to their location
    pcid: Observations identified by the curator of a project. If the ``project_id`` parameter
        is also specified, this will only consider observations identified by curators of the
        specified project(s)
    photos: Observations with photos
    popular: Observations that have been favorited by at least one user
    sounds: Observations with sounds
    taxon_is_active: Observations of active taxon concepts
    threatened: Observations whose taxa are threatened in their location
    verifiable: Observations with a ``quality_grade`` of either ``needs_id`` or ``research``.
        Equivalent to ``quality_grade=needs_id,research``
    id: Must have this ID
    not_id: Must not have this ID
    place_id: Must be observed within the place with this ID
    project_id: Must be added to the project this ID or slug
    rank: Taxon must have this rank
    site_id: Must be affiliated with the iNaturalist network website with this ID
    ofv_datatype: Must have an observation field value with this datatype
    sound_license: Must have at least one sound with this license
    without_taxon_id: Exclude observations of these taxa and their descendants
    user_id: User must have this ID or login
    user_login: User must have this login
    term_id: Must have an annotation using this controlled term ID
    term_value_id: Must have an annotation using this controlled value ID.
        Must be combined with the ``term_id`` parameter
    without_term_value_id: Exclude observations with annotations using this controlled value ID.
        Must be combined with the ``term_id`` parameter
    acc_above: Must have an positional accuracy above this value (meters)
    acc_below: Must have an positional accuracy below this value (meters)
    created_d1: Must be created at or after this time
    created_d2: Must be created at or before this time
    created_on: Must be created on this date
    observed_on: Must be observed on this date
    unobserved_by_user_id: Must not be of a taxon previously observed by this user
    apply_project_rules_for: Must match the rules of the project with this ID or slug
    cs: Taxon must have this conservation status code. If the ``place_id`` parameter is also
        specified, this will only consider statuses specific to that place
    csa: Taxon must have a conservation status from this authority. If the ``place_id`` parameter is
        also specified, this will only consider statuses specific to that place
    csi: Taxon must have this IUCN conservation status. If the ``place_id`` parameter is also
        specified, this will only consider statuses specific to that place
    geoprivacy: Must have this geoprivacy setting
    taxon_geoprivacy: Filter observations by the most conservative geoprivacy applied by a
        conservation status associated with one of the taxa proposed in the current
        identifications.
    hrank: Taxon must have this rank or lower
    lrank: Taxon must have this rank or higher
    id_above: Must have an ID above this value
    id_below: Must have an ID below this value
    identifications: Identifications must meet these criteria
    lat: Must be within a ``radius`` kilometer circle around this lat/lng (lat, lng, radius)
    lng: Must be within a ``radius`` kilometer circle around this lat/lng (lat, lng, radius)
    radius: Must be within a {radius} kilometer circle around this lat/lng (lat, lng, radius)
    not_in_project: Must not be in the project with this ID or slug
    not_matching_project_rules_for: Must not match the rules of the project with this ID or slug
    search_on: Properties to search on, when combined with q. Searches across all properties by
        default
    viewer_id: See reviewed
    reviewed: Observations have been reviewed by the user with ID equal to the value of the
        ``viewer_id`` parameter
    locale: Locale preference for taxon common names
    preferred_place_id: Place preference for regional taxon common names
    ttl: Set the ``Cache-Control`` HTTP header with this value as ``max-age``, in seconds
    """


# Observation params that are only in the REST API
def _observation_rest_only(
    has: MultiStr = None,
    on: Date = None,
    m1: Date = None,
    m2: Date = None,
    h1: Date = None,
    h2: Date = None,
    extra: str = None,
    response_format: str = "json",
):
    """
    has: Catch-all for some boolean selectors. This can be used multiple times, e.g.
        ``has=['photos', 'geo']``
    m1: First month of a month range
    m2: Last month of a month range
    h1: First hour of an hour range
    h2: Last hour of an hour range
    on: Filter by date string
    extra: Retrieve additional information.
        **'projects'** returns info about the projects the observations have been added to,
        **'fields'** returns observation field values,
        **'observation_photos'** returns information about the photos' relationship with the
        observation, like their order.
    response_format: A supported response format to return
    """


def _create_observation(
    species_guess: str = None,
    taxon_id: int = None,
    observed_on_string: Date = None,
    time_zone: str = None,
    description: str = None,
    tag_list: MultiStr = None,
    place_guess: str = None,
    latitude: float = None,
    longitude: float = None,
    map_scale: int = None,
    positional_accuracy: int = None,
    geoprivacy: str = None,
    observation_fields: ObsFieldValues = None,
    observation_field_values_attributes: ObsFieldValues = None,
    flickr_photos: MultiInt = None,
    picasa_photos: MultiStr = None,
    facebook_photos: MultiStr = None,
    local_photos: Iterable[FileOrPath] = None,
):
    """
    species_guess: Equivalent to the "What did you see?" field on the observation form.
        iNat will try to choose a single taxon based on this, but it may fail if it's ambuguous
    taxon_id: ID of the taxon to associate with this observation
    observed_on_string: Date/time of the observation. Time zone will default to the user's
        time zone if not specified.
    time_zone: Time zone the observation was made in
    description: Observation description
    tag_list: Comma-separated list of tags
    place_guess: Name of the place where the observation was recorded.
        **Note:** iNat will *not* try to automatically look up coordinates based on this string
    latitude: Latitude of the observation; presumed datum is **WGS84**
    longitude: Longitude of the observation; presumed datum is **WGS84**
    map_scale: Google Maps zoom level (from **0 to 19**) at which to show this observation's map marker.
    positional_accuracy: Positional accuracy of the observation coordinates, in meters
    geoprivacy: Geoprivacy for the observation
    observation_fields: Dict of observation fields in the format ``{id: value}``.
        Alias for ``observation_field_values_attributes``.
    flickr_photos: Flickr photo ID(s) to add as photos for this observation. User must have
        their Flickr and iNat accounts connected, and the user must own the photo(s) on Flickr.
    picasa_photos: Picasa photo ID(s) to add as photos for this observation. User must have
        their Picasa and iNat accounts connected, and the user must own the photo(s) on Picasa.
    facebook_photos: Facebook photo IDs to add as photos for this observation. User must have
        their Facebook and iNat accounts connected, and the user must own the photo on Facebook.
    local_photos: Image files, file-like objects, and/or paths for local photos to upload
    """


def _update_observation(
    # _method: str = None,  # Exposed as a client-specific workaround; not needed w/ `requests`
    ignore_photos: bool = True,
):
    """
    ignore_photos
        If photos exist on the observation but are missing in the request, simply ignore them
        instead of deleting the missing observation photos
    """


# Projects
# --------------------


# Note: 'page' parameter is not in API docs, but it appears to work. 'order' does not, however.
def _projects_params(
    q: str = None,
    id: MultiInt = None,
    not_id: MultiInt = None,
    lat: float = None,
    lng: float = None,
    radius: int = 500,
    featured: bool = None,
    noteworthy: bool = None,
    site_id: int = None,
    rule_details: bool = None,
    type: MultiStr = None,
    member_id: int = None,
    has_params: bool = None,
    has_posts: bool = None,
):
    """
    q: Project name must begin with this value
    id: Must have this ID
    not_id: Must not have this ID
    lat: Must be within a ``radius`` kilometer circle around this lat/lng
    lng: Must be within a ``radius`` kilometer circle around this lat/lng
    radius: Distance from center (``(lat, lng)``) to search, in kilometers. Defaults to 500km.
    featured:  Must be marked featured for the relevant site
    noteworthy: Must be marked noteworthy for the relevant site
    site_id: Site ID that applies to ``featured`` and ``noteworthy``.
        Defaults to the site of the authenticated user, or to the main iNaturalist site
    rule_details: Return more information about project rules, for example return a full taxon
        object instead of simply an ID
    type: Projects must be of this type
    member_id: Project must have member with this user ID
    has_params: Must have search parameter requirements
    has_posts: Must have posts
    per_page: Number of results to return in a page. The maximum value is generally 200 unless otherwise noted
    order_by: Sort order.
        ``distance`` only applies if lat and lng are specified.
        ``featured`` only applies if ``featured`` or ``noteworthy`` are true.
    """


# Taxa
# --------------------


def _taxon_params(
    q: str = None,
    is_active: bool = None,
    taxon_id: int = None,
    rank: str = None,
    max_rank: str = None,
    min_rank: str = None,
    rank_level: int = None,
    locale: str = None,
    preferred_place_id: int = None,
    all_names: bool = None,
    per_page: int = None,
):
    """
    q: Name must begin with this value
    is_active: Taxon is active
    taxon_id: Only show taxa with this ID, or its descendants
    rank: Taxon must have this exact rank
    min_rank: Taxon must have this rank or higher; overrides ``rank``
    max_rank: Taxon must have this rank or lower; overrides ``rank``
    rank_level: Taxon must have this rank level. Some example values are 70 (kingdom), 60 (phylum),
        50 (class), 40 (order), 30 (family), 20 (genus), 10 (species), 5 (subspecies)
    locale: Locale preference for taxon common names
    preferred_place_id: Place preference for regional taxon common names
    all_names: Include all taxon names in the response
    per_page: Number of results to return in a page. The maximum value is generally 200 unless
        otherwise noted
    """


def _taxon_id_params(
    id_above: int = None,
    id_below: int = None,
    only_id: int = None,
    parent_id: int = None,
):
    """
    id_above: Must have an ID above this value
    id_below: Must have an ID below this value
    only_id: Return only the record IDs
    parent_id: Taxon's parent must have this ID
    """


# Individual/common params
# ------------------------


def _access_token(access_token: str = None):
    """
    access_token: An access token required for user authentication, as returned by
        :py:func:`get_access_token()`
    """


def _bounding_box(
    nelat: float = None,
    nelng: float = None,
    swlat: float = None,
    swlng: float = None,
):
    """
    nelat: NE latitude of bounding box
    nelng: NE longitude of bounding box
    swlat: SW latitude of bounding box
    swlng: SW longitude of bounding box
    """


def _geojson_properties(properties: List[str] = None):
    """
    properties: Properties from observation results to include as GeoJSON properties
    """


def _minify(minify: str = None):
    """
    minify: Condense each match into a single string containing taxon ID, rank, and name
    """


def _name(name: str = None):
    """
    name: Name must match this value
    """


def _only_id(only_id: bool = False):
    """
    only_id: Return only the record IDs
    """


def _observation_id(observation_id: int):
    """
    observation_id: iNaturalist observation ID
    """


def _page(page: int = None):
    """
    page: Page number of results to return
    """


def _pagination(
    page: int = None,
    per_page: int = None,
    order: str = None,
    order_by: str = None,
):
    """
    page: Page number of results to return
    per_page: Number of results to return in a page. The maximum value is generally 200,
        unless otherwise noted
    order: Sort order
    order_by: Field to sort on
    """


_get_observations = [
    _observation_common,
    _observation_node_only,
    _bounding_box,
]


def _search_query(q: str = None):
    """
    q: Search query
    """


def _format_param_choices():
    return "\n".join(
        [f"  * {param}: {choices}" for param, choices in MULTIPLE_CHOICE_PARAMS.items()]
    )


MULTIPLE_CHOICE_PARAM_DOCS = "**Multiple-Choice Parameters:**\n" + _format_param_choices()
