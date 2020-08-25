"""
Reusable template functions + utilities used for API documentation.
Each template function contains a portion of an endpoint's request parameters, with corresponding
type annotations and docstrings.

Example usage::

    # 1. Template function with individual request params + docs
    >>> def get_foo_template(arg_1: str = None, arg_2: bool = False):
    >>>     '''
    >>>     arg_1: Example request parameter 1
    >>>     arg_2: Example request parameter 2
    >>>     '''

    # 2. API Endpoint function with generic (variadic) keyword args
    >>> @document_request_params(get_foo_template)
    >>> def get_foo(**kwargs) -> List:
        ''' Get Foo resource '''

    # 3. Modified function signature + docstring
    >>> help(get_foo)
    '''
    Help on function get_foo:

    get_foo(arg_1: str = None, arg_2: bool = False) -> List
      Get Foo resource

      Args:
          arg_1: Example request parameter 1
          arg_2: Example request parameter 2
    '''
"""
from inspect import cleandoc
from itertools import chain
from functools import wraps
from logging import getLogger
from typing import Callable, Dict, List

from pyinaturalist.constants import (
    MultiInt,
    MultiStr,
    Date,
    DateTime,
    IntOrStr,
    TemplateFunction,
)
from pyinaturalist.request_params import MULTIPLE_CHOICE_PARAMS

logger = getLogger(__name__)


def document_request_params(template_functions: List[TemplateFunction]):
    """ Document a function with both docstrings and function signatures from one or more
    template functions.

    Signature modification requires ``forge``. If not installed, only docstrings will be modified.

    Args:
        template_functions: Template functions containing docstrings and params to apply to the
            wrapped function
    """
    template_functions += [user_agent]

    def f(func):
        # Modify docstring
        func = copy_docstrings(func, template_functions)

        # If forge is installed, modify signature; otherwise, silently ignore it
        try:
            func = copy_signatures(func, template_functions)
        except ImportError:
            logger.debug("Forge not installed; skipping runtime API documentation")

        # Call modified function
        @wraps(func)
        def g(*args, **kwargs):
            return func(*args, **kwargs)

        return g

    return f


def copy_docstrings(
    target_function: Callable, template_functions: List[TemplateFunction]
) -> Callable:
    """ Copy docstrings from one or more template functions to a target function.
    Assumes Google-style docstrings.

    Args:
        target_function: Function to modify
        template_functions: Functions containing docstrings to apply to ``target_function``
    """
    # Start with initial function description only
    docstring, return_value_desc = _split_docstring(target_function.__doc__ or "")

    # Insert 'Args' section
    docstring += "\n\nArgs:"
    for template_function in template_functions:
        docstring += template_function.__doc__ or ""
        docstring = docstring.rstrip()

    # Insert 'Returns' section, if present
    if return_value_desc:
        docstring += "\n\nReturns:\n    " + return_value_desc

    target_function.__doc__ = docstring
    return target_function


def _split_docstring(docstring):
    """ Split a docstring into a function description + return value description, if present. """
    if "Returns:" in docstring:
        function_desc, return_value_desc = docstring.split("Returns:")
    else:
        function_desc = docstring
        return_value_desc = ""

    return cleandoc(function_desc.strip()), cleandoc(return_value_desc.strip())


def copy_signatures(
    target_function: Callable, template_functions: List[TemplateFunction]
) -> Callable:
    """ Copy function signatures from one or more template functions to a target function.

    Args:
        target_function: Function to modify
        template_functions: Functions containing params to apply to ``target_function``
    """
    revision = _get_combined_revision(template_functions)
    return revision(target_function)


def _get_combined_revision(template_functions: List[TemplateFunction]):
    """ Create a :py:class:`forge.Revision` from the combined parameters of multiple functions """
    import forge

    # Use forge.copy to create a revision for each template function
    revisions = [forge.copy(func) for func in template_functions]

    # Combine the parameters of all revisions into a single revision
    fparams = [list(rev.signature.parameters.values()) for rev in revisions]
    return forge.sign(*list(chain.from_iterable(fparams)))


def observation_params(
    params: Dict = None,
    acc: bool = None,
    captive: bool = None,
    endemic: bool = None,
    geo: bool = None,
    id_please: bool = None,
    identified: bool = None,
    introduced: bool = None,
    mappable: bool = None,
    native: bool = None,
    out_of_range: bool = None,
    pcid: bool = None,
    photos: bool = None,
    popular: bool = None,
    sounds: bool = None,
    taxon_is_active: bool = None,
    threatened: bool = None,
    verifiable: bool = None,
    id: MultiInt = None,
    not_id: MultiInt = None,
    license: MultiStr = None,
    photo_license: MultiStr = None,
    sound_license: MultiStr = None,
    ofv_datatype: MultiStr = None,
    place_id: MultiInt = None,
    project_id: MultiInt = None,
    rank: MultiStr = None,
    site_id: MultiStr = None,
    taxon_id: MultiInt = None,
    without_taxon_id: MultiInt = None,
    taxon_name: MultiStr = None,
    user_id: MultiInt = None,
    user_login: MultiStr = None,
    day: MultiInt = None,
    month: MultiInt = None,
    year: MultiInt = None,
    term_id: MultiInt = None,
    term_value_id: MultiInt = None,
    without_term_value_id: MultiInt = None,
    acc_above: str = None,
    acc_below: str = None,
    d1: Date = None,
    d2: Date = None,
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
    iconic_taxa: MultiStr = None,
    id_above: int = None,
    id_below: int = None,
    identifications: str = None,
    lat: float = None,
    lng: float = None,
    radius: float = None,
    list_id: int = None,
    not_in_project: IntOrStr = None,
    not_matching_project_rules_for: IntOrStr = None,
    q: str = None,
    search_on: str = None,
    quality_grade: str = None,
    updated_since: DateTime = None,
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
    out_of_range: Observations whose taxa are outside their known ranges
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
        Must be combined with the ``term_id`` parameter
    without_term_value_id: Exclude observations with annotations using this controlled value ID.
        Must be combined with the ``term_id`` parameter
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
    iconic_taxa: Taxon must by within this iconic taxon
    id_above: Must have an ID above this value
    id_below: Must have an ID below this value
    identifications: Identifications must meet these criteria
    lat: Must be within a ``radius`` kilometer circle around this lat/lng (lat, lng, radius)
    lng: Must be within a ``radius`` kilometer circle around this lat/lng (lat, lng, radius)
    radius: Must be within a {radius} kilometer circle around this lat/lng (lat, lng, radius)
    list_id: Taxon must be in the list with this ID
    not_in_project: Must not be in the project with this ID or slug
    not_matching_project_rules_for: Must not match the rules of the project with this ID or slug
    q: Search observation properties. Can be combined with ``search_on``
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


def taxon_params(
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


def taxon_id_params(
    id_above: int = None, id_below: int = None, only_id: int = None, parent_id: int = None,
):
    """
    id_above: Must have an ID above this value
    id_below: Must have an ID below this value
    only_id: Return only the record IDs
    parent_id: Taxon's parent must have this ID
    """


def minify(minify: str = None):
    """
    minify: Condense each match into a single string containg taxon ID, rank, and name
    """


def bounding_box(
    nelat: float = None, nelng: float = None, swlat: float = None, swlng: float = None,
):
    """
    nelat: NE latitude of bounding box
    nelng: NE longitude of bounding box
    swlat: SW latitude of bounding box
    swlng: SW longitude of bounding box
    """


def geojson_properties(properties: List[str] = None):
    """
    properties: Properties from observation results to include as GeoJSON properties
    """


def name(name: str = None):
    """
    name: Name must match this value
    """


def only_id(only_id: bool = False):
    """
    only_id: Return only the record IDs
    """


def pagination(
    page: int = None, per_page: int = None, order: str = None, order_by: str = None,
):
    """
    page: Pagination page number
    per_page: Number of results to return in a page. The maximum value is generally 200,
        unless otherwise noted
    order: Sort order
    order_by: Field to sort on
    """


def user_agent(user_agent: str = None):
    """
    user_agent: A custom user-agent string to provide to the iNaturalist API
    """


def _format_param_choices():
    return "\n".join(
        ["  * {}: {}".format(param, choices) for param, choices in MULTIPLE_CHOICE_PARAMS.items()]
    )


# Request param combinations for specific API endpoints
get_observations_params = [observation_params, bounding_box, pagination, only_id]
get_all_observations_params = [observation_params, bounding_box, only_id]
get_observation_species_counts_params = [observation_params, bounding_box]
get_geojson_observations_params = [observation_params, bounding_box, geojson_properties]
get_places_nearby_params = [bounding_box, name]
get_taxa_params = [taxon_params, taxon_id_params]
get_taxa_autocomplete_params = [taxon_params, minify]


MULTIPLE_CHOICE_PARAM_DOCS = "**Multiple-Choice Parameters:**\n" + _format_param_choices()
