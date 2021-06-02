from pyinaturalist import api_docs as docs
from pyinaturalist.constants import PROJECT_ORDER_BY_PROPERTIES, JsonResponse, MultiInt
from pyinaturalist.forge_utils import document_request_params
from pyinaturalist.pagination import add_paginate_all
from pyinaturalist.request_params import validate_multiple_choice_param
from pyinaturalist.response_format import convert_all_coordinates, convert_all_timestamps
from pyinaturalist.v1 import get_v1


@document_request_params([docs._projects_params, docs._pagination])
@add_paginate_all(method='page')
def get_projects(**params) -> JsonResponse:
    """Given zero to many of following parameters, get projects matching the search criteria.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Projects/get_projects

    Example:

        Search for projects about invasive species within 400km of Vancouver, BC:

        >>> response = get_projects(
        >>>     q='invasive',
        >>>     lat=49.27,
        >>>     lng=-123.08,
        >>>     radius=400,
        >>>     order_by='distance',
        >>> )

        Show basic info for projects in response:

        >>> print(format_projects(response, align=True))
        [8291    ] PNW Invasive Plant EDDR
        [19200   ] King County (WA) Noxious and Invasive Weeds
        [102925  ] Keechelus/Kachess Invasive Plants
        ...


        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_projects.py

    Returns:
        Response dict containing project records
    """
    validate_multiple_choice_param(params, 'order_by', PROJECT_ORDER_BY_PROPERTIES)
    r = get_v1('projects', params=params)
    r.raise_for_status()

    response = r.json()
    response['results'] = convert_all_coordinates(response['results'])
    response['results'] = convert_all_timestamps(response['results'])
    return response


def get_projects_by_id(
    project_id: MultiInt, rule_details: bool = None, user_agent: str = None
) -> JsonResponse:
    """Get one or more projects by ID.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Projects/get_projects_id

    Example:

        >>> response = get_projects_by_id([8348, 6432])
        >>> print(format_projects(response))
        [8348] Tucson High Native and Invasive Species Inventory
        [6432] CBWN Invasive Plants

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_projects_by_id.py

    Args:
        project_id: Get projects with this ID. Multiple values are allowed.
        rule_details: Return more information about project rules, for example return a full taxon
            object instead of simply an ID

    Returns:
        Response dict containing project records
    """
    r = get_v1(
        'projects',
        ids=project_id,
        params={'rule_details': rule_details},
        user_agent=user_agent,
    )
    r.raise_for_status()

    response = r.json()
    response['results'] = convert_all_coordinates(response['results'])
    response['results'] = convert_all_timestamps(response['results'])
    return response
