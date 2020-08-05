""" Reusable template functions used to define API request parameters """
from itertools import chain
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

logger = getLogger(__name__)


def copy_signatures(
    target_function: Callable, template_functions: List[TemplateFunction]
) -> Callable:
    """ Copy function signatures from one or more template functions to a target function.

    Args:
        target_function: Function to modify
        template_function: Functions containing params to apply to ``target_function``
    """
    template_functions += [user_agent]
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


def observation_params_template(
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
    nelat: float = None,
    nelng: float = None,
    swlat: float = None,
    swlng: float = None,
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
    pass


def pagination_params(
    page: int = None, per_page: int = None, order: str = None, order_by: str = None,
):
    pass


def geojson_properties(properties: List[str] = None):
    pass


def only_id(only_id: bool = False):
    pass


def user_agent(user_agent: str = None):
    pass


def user_id(user_agent: str = None):
    pass


# Request param combinations for specific API endpoints
get_observations_params = [observation_params_template, pagination_params, only_id]
get_all_observations_params = [observation_params_template, only_id]
get_observation_species_counts_params = [observation_params_template]
get_geojson_observations_params = [observation_params_template, geojson_properties]
