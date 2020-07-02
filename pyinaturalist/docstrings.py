""" Reusable portions of API documentation, to help reduce verbosity of particularly long lists of
request parameter descriptions.
"""
from typing import Callable, List


def append(func: Callable, doc_chunks: List[str]):
    """ Append information to a function's docstring """
    func.__doc__ = func.__doc__ or ""  # Makes type checker happy
    for chunk in doc_chunks:
        func.__doc__ += chunk


GET_OBSERVATIONS = """
Args:
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
    out_of_range: Observations whose taxa are outside their known ranges
    pcid: Observations identified by the curator of a project. If the project_id parameter
        is also specified, this will only consider observations identified by curators of the
        specified project(s)
    photos: Observations with photos
    popular: Observations that have been favorited by at least one user
    sounds: Observations with sounds
    taxon_is_active: Observations of active taxon concepts
    threatened: Observations whose taxa are threatened in their location
    verifiable: Observations with a quality_grade of either needs_id or research. Equivalent to quality_grade=needs_id,research
    id: Must have this ID
    not_id: Must not have this ID
    license: Observation must have this license
    ofv_datatype: Must have an observation field value with this datatype
    photo_license: Must have at least one photo with this license
    place_id: Must be observed within the place with this ID
    project_id: Must be added to the project this ID or slug
    rank: Taxon must have this rank
    site_id: Must be affiliated with the iNaturalist network website with this ID
    sound_license: Must have at least one sound with this license
    taxon_id: Only show observations of these taxa and their descendants
    without_taxon_id: Exclude observations of these taxa and their descendants
    taxon_name: Taxon must have a scientific or common name matching this string
    user_id: User must have this ID or login
    user_login: User must have this login
    day: Must be observed within this day of the month
    month: Must be observed within this month
    year: Must be observed within this year
    term_id: Must have an annotation using this controlled term ID
    term_value_id: Must have an annotation using this controlled value ID.
        Must be combined with the term_id parameter
    without_term_value_id: Exclude observations with annotations using this controlled value ID.
        Must be combined with the term_id parameter
    acc_above: Must have an positional accuracy above this value (meters)
    acc_below: Must have an positional accuracy below this value (meters)
    d1: Must be observed on or after this date
    d2: Must be observed on or before this date
    created_d1: Must be created at or after this time
    created_d2: Must be created at or before this time
    created_on: Must be created on this date
    observed_on: Must be observed on this date
    unobserved_by_user_id: Must not be of a taxon previously observed by this user
    apply_project_rules_for: Must match the rules of the project with this ID or slug
    cs: Taxon must have this conservation status code. If the place_id parameter is also
        specified, this will only consider statuses specific to that place
    csa: Taxon must have a conservation status from this authority. If the place_id parameter is
        also specified, this will only consider statuses specific to that place
    csi: Taxon must have this IUCN conservation status. If the place_id parameter is also
        specified, this will only consider statuses specific to that place
    geoprivacy: Must have this geoprivacy setting
    taxon_geoprivacy: Filter observations by the most conservative geoprivacy applied by a
        conservation status associated with one of the taxa proposed in the current
        identifications.
    hrank: Taxon must have this rank or lower
    lrank: Taxon must have this rank or higher
    iconic_taxa: Taxon must by within this iconic taxon
    id_above: Must have an ID above this value
    id_below: Must have an ID below this value
    identifications: Identifications must meet these criteria
    lat: Must be within a ``radius`` kilometer circle around this lat/lng (lat, lng, radius)
    lng: Must be within a ``radius`` kilometer circle around this lat/lng (lat, lng, radius)
    radius: Must be within a {radius} kilometer circle around this lat/lng (lat, lng, radius)
    nelat: NE latitude of bounding box
    nelng: NE longitude of bounding box
    swlat: SW latitude of bounding box
    swlng: SW longitude of bounding box
    list_id: Taxon must be in the list with this ID
    not_in_project: Must not be in the project with this ID or slug
    not_matching_project_rules_for: Must not match the rules of the project with this ID or slug
    q: Search observation properties. Can be combined with search_on
    search_on: Properties to search on, when combined with q. Searches across all properties by
        default
    quality_grade: Must have this quality grade
    updated_since: Must be updated since this time
    viewer_id: See reviewed
    reviewed: Observations have been reviewed by the user with ID equal to the value of the
        ``viewer_id`` parameter
    locale: Locale preference for taxon common names
    preferred_place_id: Place preference for regional taxon common names
    ttl: Set the ``Cache-Control`` HTTP header with this value as ``max-age``, in seconds
"""
