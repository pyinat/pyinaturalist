"""Reusable template functions used for API documentation.
Each template function contains all or part of an endpoint's request parameters, type annotations,
and docstrings. These are then applied with :py:func:`.copy_doc_signature`.

This is intended to reduce large amounts of duplicated function signatures and corresponding
docstrings. If you're a contributor looking to add a new endpoint, using these templates isn't
necessary. If the new function(s) have a large number of parameters and/or have many parameters in
common with other functions, consider using a template function.

Note: Since the templates are applied dynamically at import time, this adds a tiny amount of overhead
(about 20 milliseconds as of v0.14) to the import time of the library.
"""

# ruff: noqa: E501
from typing import Any

from pyinaturalist.constants import (
    AnyDate,
    AnyDateTime,
    DateOrStr,
    IntOrStr,
    MultiFile,
    MultiInt,
    MultiIntOrStr,
    MultiStr,
    ObsFieldValues,
)

# Identifications
# --------------------


def _identification_params(
    current_taxon: bool | None = None,
    own_observation: bool | None = None,
    is_change: bool | None = None,
    taxon_active: bool | None = None,
    observation_taxon_active: bool | None = None,
    id: MultiInt | None = None,
    rank: MultiStr | None = None,
    observation_rank: MultiStr | None = None,
    user_id: MultiIntOrStr | None = None,
    user_login: MultiStr | None = None,
    current: bool | None = None,
    category: MultiStr | None = None,
    place_id: MultiInt | None = None,
    quality_grade: MultiStr | None = None,
    taxon_id: MultiInt | None = None,
    observation_taxon_id: MultiInt | None = None,
    iconic_taxon_id: MultiInt | None = None,
    observation_iconic_taxon_id: MultiInt | None = None,
    lrank: str | None = None,
    hrank: str | None = None,
    observation_lrank: str | None = None,
    observation_hrank: str | None = None,
    without_taxon_id: MultiInt | None = None,
    without_observation_taxon_id: MultiInt | None = None,
    d1: AnyDate | None = None,
    d2: AnyDate | None = None,
    observation_created_d1: AnyDate | None = None,
    observation_created_d2: AnyDate | None = None,
    observed_d1: AnyDate | None = None,
    observed_d2: AnyDate | None = None,
    id_above: int | None = None,
    id_below: int | None = None,
):
    """Args:
    current_taxon: ID's taxon is the same it's observation's taxon
    own_observation: ID was added by the observer
    is_change: ID was created as a results of a taxon change
    taxon_active: ID's taxon is currently an active taxon
    observation_taxon_active: Observation's taxon is currently an active taxon
    id: Identification ID
    rank: ID's taxon must have this rank  # Multiple choice
    observation_rank: Observation's taxon must have this rank  # Multiple choice
    user_id: Identifier must have this user ID
    user_login: Identifier must have this user login
    current: Most recent Identification on a observation by a user
    category: Type of identification
    place_id: Observation must occur in this place
    quality_grade: Observation must have this quality grade
    taxon_id: Identification taxa must match the given taxa or their descendants
    observation_taxon_id: Observation taxa must match the given taxa or their descendants
    iconic_taxon_id: Identification iconic taxon ID
    observation_iconic_taxon_id: Observation iconic taxon ID
    lrank: Identification taxon must have this rank or higher
    hrank: Identification taxon must have this rank or lower
    observation_lrank: Observation taxon must have this rank or higher
    observation_hrank: Observation taxon must have this rank or lower
    without_taxon_id: Exclude Identifications of these taxa and their descendants
    without_observation_taxon_id: Exclude Identifications of observations of these taxa and their descendants
    d1: Must be observed on or after this date
    d2: Must be observed on or before this date
    observation_created_d1: Observation must be created on or after this date
    observation_created_d2: Observation must be created on or before this date
    observed_d1: Observation must be observed on or after this date
    observed_d2: Observation must be observed on or before this date
    id_above: Must have an ID above this value
    id_below: Must have an ID below this value
    """


# Messages
# --------------------


def _message_params(
    page: int | None = None,
    box: str | None = None,
    q: str | None = None,
    user_id: int | None = None,
    threads: bool = False,
):
    """Args:
    page: Page number of the results to return
    box: One of 'inbox', 'sent', or 'any'
    q: Search string for message subject and body
    user_id: Get messages to/from this user
    threads: Group results by ``thread_id``, and only get the latest message per thread.
        Incompatible with ``q`` param.
    """


def _message_id(message_id: int):
    """Args:
    message_id: Get the message with this ID. Multiple IDs are allowed.
    """


# Observations
# --------------------


# Params that are in most observation-related endpoints in all API versions
def _observation_common(
    q: str | None = None,
    d1: AnyDate | None = None,
    d2: AnyDate | None = None,
    day: MultiInt | None = None,
    month: MultiInt | None = None,
    year: MultiInt | None = None,
    license: MultiStr | None = None,
    list_id: int | None = None,
    photo_license: MultiStr | None = None,
    out_of_range: bool | None = None,
    quality_grade: str | None = None,
    id: MultiInt | None = None,
    taxon_id: MultiInt | None = None,
    taxon_name: MultiStr | None = None,
    iconic_taxa: MultiStr | None = None,
    updated_since: AnyDateTime | None = None,
):
    """Args:
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
    id: Must have this observation ID
    taxon_id: Only show observations of these taxa and their descendants
    taxon_name: Taxon must have a scientific or common name matching this string
    iconic_taxa: Taxon must by within this iconic taxon
    updated_since: Must be updated since this time
    """


# Observation params that are only in the v1 API
def _observation_v1(
    acc: bool | None = None,
    captive: bool | None = None,
    endemic: bool | None = None,
    geo: bool | None = None,
    id_please: bool | None = None,
    identified: bool | None = None,
    introduced: bool | None = None,
    mappable: bool | None = None,
    native: bool | None = None,
    pcid: bool | None = None,
    photos: bool | None = None,
    popular: bool | None = None,
    sounds: bool | None = None,
    taxon_is_active: bool | None = None,
    threatened: bool | None = None,
    verifiable: bool | None = None,
    not_id: MultiInt | None = None,
    sound_license: MultiStr | None = None,
    observation_fields: list | dict | None = None,
    ofv_datatype: MultiStr | None = None,
    place_id: MultiInt | None = None,
    project_id: MultiInt | None = None,
    rank: MultiStr | None = None,
    site_id: MultiStr | None = None,
    without_taxon_id: MultiInt | None = None,
    user_id: MultiIntOrStr | None = None,
    user_login: MultiStr | None = None,
    ident_user_id: MultiIntOrStr | None = None,
    term_id: MultiInt | None = None,
    term_value_id: MultiInt | None = None,
    without_term_value_id: MultiInt | None = None,
    acc_above: str | None = None,
    acc_below: str | None = None,
    acc_below_or_unknown: str | None = None,
    created_d1: AnyDateTime | None = None,
    created_d2: AnyDateTime | None = None,
    created_on: AnyDate | None = None,
    observed_on: AnyDate | None = None,
    unobserved_by_user_id: int | None = None,
    apply_project_rules_for: str | None = None,
    cs: str | None = None,
    csa: str | None = None,
    csi: MultiStr | None = None,
    geoprivacy: MultiStr | None = None,
    taxon_geoprivacy: MultiStr | None = None,
    max_rank: str | None = None,
    min_rank: str | None = None,
    hrank: str | None = None,
    lrank: str | None = None,
    id_above: int | None = None,
    id_below: int | None = None,
    identifications: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    radius: float | None = None,
    not_in_project: IntOrStr | None = None,
    not_matching_project_rules_for: IntOrStr | None = None,
    search_on: str | None = None,
    viewer_id: int | None = None,
    reviewed: bool | None = None,
    locale: str | None = None,
    preferred_place_id: int | None = None,
    ttl: str | None = None,
):
    """Args:
    acc: Whether or not positional accuracy / coordinate uncertainty has been specified
    captive: Captive or cultivated observations
    endemic: Observations whose taxa are endemic to their location
    geo: Observations that are georeferenced
    id_please: Observations with the **deprecated** 'ID, Please!' flag.
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
    not_id: Must not have this ID
    place_id: Must be observed within the place with this ID
    project_id: Must be added to the project this ID or slug
    rank: Taxon must have this rank
    site_id: Must be affiliated with the iNaturalist network website with this ID
    observation_fields: Must have these observation fields (optionally with values)
    ofv_datatype: Must have an observation field value with this datatype
    sound_license: Must have at least one sound with this license
    without_taxon_id: Exclude observations of these taxa and their descendants
    user_id: Observer must have this user ID or login
    user_login: Observer must have this user login
    ident_user_id: Identifier must have this user ID or login
    term_id: Must have an annotation using this controlled term ID
    term_value_id: Must have an annotation using this controlled value ID.
        Must be combined with the ``term_id`` parameter
    without_term_value_id: Exclude observations with annotations using this controlled value ID.
        Must be combined with the ``term_id`` parameter
    acc_above: Must have an positional accuracy above this value (meters)
    acc_below: Must have an positional accuracy below this value (meters)
    acc_below_or_unknown: Must have an positional accuracy below this value (meters) or unknown
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


# Observation params that are only in the v0 API
def _observation_v0(
    has: MultiStr | None = None,
    on: AnyDate | None = None,
    m1: AnyDate | None = None,
    m2: AnyDate | None = None,
    h1: AnyDate | None = None,
    h2: AnyDate | None = None,
    extra: str | None = None,
    response_format: str = 'json',
):
    """Args:
    has: Catch-all for some boolean selectors. This can be used multiple times, e.g.
        ``has=['photos', 'geo']``
    m1: First month of a month range
    m2: Last month of a month range
    h1: First hour of an hour range
    h2: Last hour of an hour range
    on: Filter by date string
    extra: Retrieve additional information.
        **'projects'** returns info about the projects the observations have been added to,
        **'observation_fields'** returns observation field values,
        **'observation_photos'** returns information about the photos' relationship with the
        observation, like their order.
    response_format: A supported response format to return
    """


# Observation params that are only in the v2 API
def _observation_v2(
    fields: list[str] | dict[str, Any] | None = None,
    except_fields: list[str] | None = None,
):
    """Args:
    fields: Data fields to return in the response
    except_fields: Data fields to exclude from the response (and include all others)
    """


def _observation_histogram(
    date_field: str = 'observed',
    interval: str = 'month_of_year',
):
    """Args:
    date_field: Histogram basis: either when the observation was created or observed
    interval: Time interval for histogram, with groups starting on or contained within the group value.
    """


def _ofvs(observation_id: int, observation_field_id: int, value: Any):
    """Args:
    observation_id: ID of the observation receiving this observation field value
    observation_field_id: ID of the observation field for this observation field value
    value: Value for the observation field
    """


def _create_observation(
    species_guess: str | None = None,
    taxon_id: int | None = None,
    observed_on: AnyDate | None = None,
    observed_on_string: AnyDate | None = None,
    time_zone: str | None = None,
    description: str | None = None,
    tag_list: MultiStr | None = None,
    place_guess: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    map_scale: int | None = None,
    positional_accuracy: int | None = None,
    geoprivacy: str | None = None,
    observation_fields: ObsFieldValues | None = None,
    observation_field_values_attributes: ObsFieldValues | None = None,
    flickr_photos: MultiInt | None = None,
    picasa_photos: MultiStr | None = None,
    facebook_photos: MultiStr | None = None,
    local_photos: MultiFile | None = None,
    photos: MultiFile | None = None,
    sounds: MultiFile | None = None,
    photo_ids: MultiIntOrStr | None = None,
):
    """Args:
    species_guess: Equivalent to the 'What did you see?' field on the observation form.
        iNat will try to choose a single taxon based on this, but it may fail if it's ambiguous
    taxon_id: ID of the taxon to associate with this observation
    observed_on: Alias for ``observed_on_string``; accepts :py:class:`~datetime.datetime` objects.
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
    photos: One or more image files, file-like objects, file paths, or URLs
    sounds: One or more sound files, file-like objects, file paths, or URLs
    photo_ids: One or more IDs of previously uploaded photos to attach to the observation
    """


def _create_observation_v2(
    captive_flag: bool | None = None,
    coordinate_system: str | None = None,
    geo_x: float | None = None,
    geo_y: float | None = None,
    license: str | None = None,
    location_is_exact: bool | None = None,
    make_license_default: bool | None = None,
    make_licenses_same: bool | None = None,
    owners_identification_from_vision: bool | None = None,
    positioning_device: str | None = None,
    positioning_method: str | None = None,
    prefers_community_taxon: bool | None = None,
    project_id: int | None = None,
    site_id: int | None = None,
    uuid: str | None = None,
):
    """Args:
    captive_flag: Mark observation as captive/cultivated
    coordinate_system: Coordinate system used (if not WGS84)
    geo_x: X coordinate in alternative coordinate system
    geo_y: Y coordinate in alternative coordinate system
    license: License to apply to the observation (e.g., 'cc-by', 'cc-by-nc', 'cc0')
    location_is_exact: Whether the location coordinates are exact
    make_license_default: Make this license the user's default for future observations
    make_licenses_same: Apply the same license to all associated photos
    owners_identification_from_vision: Initial identification came from computer vision
    positioning_device: Device used for positioning (e.g., 'gps', 'cell', 'network')
    positioning_method: Method used to determine positioning
    prefers_community_taxon: User preference for using community taxon over their own identification
    project_id: Project ID to add observation to upon creation
    site_id: iNaturalist network site ID (e.g., for iNaturalist.ca, iNaturalist.nz)
    uuid: UUID of the observation (for updates to preserve UUID)
    """


def _update_observation(
    # _method: str = None,  # Exposed as a client-specific workaround; not needed w/ `requests`
    ignore_photos: bool = True,
):
    """Args:
    ignore_photos: If photos exist on the observation but are missing in the request, ignore them instead of deleting the missing observation photos
    """


# Posts
# --------------------


def _get_posts(
    login: str | None = None,
    project_id: int | None = None,
    page: int | None = None,
    per_page: int | None = None,
):
    """Args:
    login: Return posts by this user
    project_id: Return posts from this project
    page: Pagination page number
    per_page: Number of results to return in a page. The maximum value is generally 200 unless otherwise noted
    """


# Projects
# --------------------


# Note: 'page' parameter is not in API docs, but it appears to work. 'order' does not, however.
def _projects_params(
    q: str | None = None,
    id: MultiInt | None = None,
    not_id: MultiInt | None = None,
    lat: float | None = None,
    lng: float | None = None,
    radius: int = 500,
    featured: bool | None = None,
    noteworthy: bool | None = None,
    place_id: MultiInt | None = None,
    site_id: int | None = None,
    rule_details: bool | None = None,
    type: MultiStr | None = None,
    member_id: int | None = None,
    has_params: bool | None = None,
    has_posts: bool | None = None,
):
    """Args:
    q: Project name must begin with this value
    id: Must have this ID
    not_id: Must not have this ID
    lat: Must be within a ``radius`` kilometer circle around this lat/lng
    lng: Must be within a ``radius`` kilometer circle around this lat/lng
    radius: Distance from center (``(lat, lng)``) to search, in kilometers. Defaults to 500km.
    featured:  Must be marked featured for the relevant site
    noteworthy: Must be marked noteworthy for the relevant site
    place_id: Must be in the place with this ID
    site_id: Site ID that applies to ``featured`` and ``noteworthy``.
        Defaults to the site of the authenticated user, or to the main iNaturalist site
    rule_details: Return more information about project rules, for example return a full taxon
        object instead of simply an ID
    type: Projects must be of this type
    member_id: Project must have member with this user ID
    has_params: Must have search parameter requirements
    has_posts: Must have posts
    order_by: Sort order.
        ``distance`` only applies if lat and lng are specified.
        ``featured`` only applies if ``featured`` or ``noteworthy`` are true.
    """


def _project_observation_params(access_token: str, project_id: int, observation_id: int):
    """Args:
    access_token: An access token required for user authentication, as returned by :py:func:`.get_access_token()`
    project_id: ID of project to add onto
    observation_id: ID of observation to add
    """


def _project_update_params(
    project_id: IntOrStr,
    cover: str | None = None,
    description: str | None = None,
    icon: str | None = None,
    preferred_banner_color: str | None = None,
    prefers_banner_contain: bool | None = None,
    prefers_hide_title: bool | None = None,
    prefers_hide_umbrella_map_flags: bool | None = None,
    prefers_rule_d1: DateOrStr | None = None,
    prefers_rule_d2: DateOrStr | None = None,
    prefers_rule_introduced: str | None = None,
    prefers_rule_members_only: str | None = None,
    prefers_rule_month: MultiStr | None = None,
    prefers_rule_native: bool | None = None,
    prefers_rule_observed_on: DateOrStr | None = None,
    prefers_rule_photos: bool | None = None,
    prefers_rule_quality_grade: MultiStr | None = None,
    prefers_rule_sounds: bool | None = None,
    prefers_rule_term_id: str | None = None,
    prefers_rule_term_value_id: str | None = None,
    prefers_user_trust: bool | None = None,
    project_type: str | None = None,
    title: str | None = None,
    user_id: int | None = None,
    admin_attributes: list[dict] | None = None,
    project_observation_rules_attributes: list[dict] | None = None,
):
    """Args:
    project_id: Numeric project ID or slug (the short name shown in project URL)
    cover: Banner image for project page; ideally 760x320 px
    description: Description shown on project page
    icon: Image used as project icon. Should be at least 72x72 px and will be cropped to a square.
    preferred_banner_color: Background color for project banner, as a RGB hex value (e.g., ``'#74ac00'``)
    prefers_banner_contain: Fit banner image without cropping
    prefers_hide_title:
    prefers_hide_umbrella_map_flags:
    prefers_rule_d1: Observation date range to include (start)
    prefers_rule_d2: Observation date range to include (end)
    prefers_rule_observed_on: Exact observation date to include
    prefers_rule_introduced: Only include observations of introduced species
    prefers_rule_native: Only include observations of native species
    prefers_rule_members_only: Only include observations of project members
    prefers_rule_month: Only include observations from these months
    prefers_rule_photos: Only include observations with photos
    prefers_rule_sounds: Only include observations with sounds
    prefers_rule_quality_grade: Only include observations with these quality grades
    prefers_rule_term_id: Only include observations with this annotation (controlled term ID)
    prefers_rule_term_value_id: Only include observations with this annotation value (controlled term value ID)
    prefers_user_trust: Only include observations from trusted users
    project_type: Project type ('umbrella' or 'collection')
    title: Project title
    user_id: User ID of project owner
    admin_attributes: Admin users and their roles
    project_observation_rules_attributes: Rules for observations to include in the project
    """


# Main Search
# --------------------


def _search_params(
    q: str,
    sources: MultiStr | None = None,  # enum
    place_id: MultiInt | None = None,
    locale: str | None = None,
    preferred_place_id: int | None = None,
):
    """Args:
    q: Search query
    sources: Object types to search
    place_id: Results must be associated with this place
    locale: Locale preference for taxon common names
    preferred_place_id: Place preference for regional taxon common names
    """


# Taxa
# --------------------


def _taxon_params(
    q: str | None = None,
    is_active: bool | None = None,
    taxon_id: int | None = None,
    rank: str | None = None,
    max_rank: str | None = None,
    min_rank: str | None = None,
    rank_level: int | None = None,
    locale: str | None = None,
    preferred_place_id: int | None = None,
    all_names: bool | None = None,
):
    """Args:
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
    """


def _taxon_id_params(
    id_above: int | None = None,
    id_below: int | None = None,
    only_id: bool | None = None,
    parent_id: int | None = None,
):
    """Args:
    id_above: Must have an ID above this value
    id_below: Must have an ID below this value
    only_id: Return only the record IDs
    parent_id: Taxon's parent must have this ID
    """


# Individual/common params
# ------------------------


def _access_token(access_token: str | None = None):
    """Args:
    access_token: An access token for user authentication, as returned by :py:func:`.get_access_token()`
    """


def _bounding_box(
    nelat: float | None = None,
    nelng: float | None = None,
    swlat: float | None = None,
    swlng: float | None = None,
):
    """Args:
    nelat: NE latitude of bounding box
    nelng: NE longitude of bounding box
    swlat: SW latitude of bounding box
    swlng: SW longitude of bounding box
    """


def _geojson_properties(properties: list[str] | None = None):
    """Args:
    properties: Properties from observation results to include as GeoJSON properties
    """


def _name(name: str | None = None):
    """Args:
    name: Name must match this value
    """


def _only_id(only_id: bool | None = None):
    """Args:
    only_id: Return only the record IDs
    """


def _observation_id(observation_id: int):
    """Args:
    observation_id: iNaturalist observation ID
    """


def _project_id(project_id: int | None = None):
    """Args:
    project_id: Only show users who are members of this project
    """


def _pagination(
    page: int | None = None,
    per_page: int | None = None,
    order: str | None = None,
    order_by: str | None = None,
    count_only: bool | None = None,
    reverse: bool | None = None,
):
    """Args:
    page: Page number of results to return
    per_page: Number of results to return in a page. The maximum value is generally 200,
        unless otherwise noted
    order: Sort order
    order_by: Field to sort on
    count_only: Only return a count of results; alias for ``per_page=0``
    reverse: Reverse the order of results; alias for ``order='descending'``
    """


_get_observations = [
    _observation_common,
    _observation_v1,
    _bounding_box,
]


def _search_query(q: str | None = None):
    """Args:
    q: Search query
    """
