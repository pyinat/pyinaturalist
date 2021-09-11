from pyinaturalist.constants import PROJECT_ORDER_BY_PROPERTIES, JsonResponse, MultiInt
from pyinaturalist.converters import convert_all_coordinates, convert_all_timestamps
from pyinaturalist.docs import document_request_params
from pyinaturalist.docs import templates as docs
from pyinaturalist.pagination import add_paginate_all
from pyinaturalist.request_params import validate_multiple_choice_param
from pyinaturalist.v1 import delete_v1, get_v1, post_v1


@document_request_params(docs._projects_params, docs._pagination)
@add_paginate_all()
def get_projects(**params) -> JsonResponse:
    """Search projects

    .. rubric:: Notes

    * API reference: :v1:`GET /projects <Projects/get_projects>`

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

        >>> pprint(response)
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
    response = get_v1('projects', **params)

    projects = response.json()
    projects['results'] = convert_all_coordinates(projects['results'])
    projects['results'] = convert_all_timestamps(projects['results'])
    return projects


def get_projects_by_id(project_id: MultiInt, rule_details: bool = None, **params) -> JsonResponse:
    """Get one or more projects by ID

    .. rubric:: Notes

    * API reference: :v1:`GET /projects/{id} <Projects/get_projects_id>`

    Example:
        >>> response = get_projects_by_id([8348, 6432])
        >>> pprint(response)
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
    response = get_v1('projects', ids=project_id, rule_details=rule_details, **params)

    projects = response.json()
    projects['results'] = convert_all_coordinates(projects['results'])
    projects['results'] = convert_all_timestamps(projects['results'])
    return projects


@document_request_params(docs._project_observation_params)
def add_project_observation(
    project_id: int, observation_id: int, access_token: str = None, **params
) -> JsonResponse:
    """Add an observation to a project

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * API reference: :v1:`POST projects/{id}/add <Projects/post_projects_id_add>`
    * API reference: :v1:`POST /project_observations <Project_Observations/post_project_observations>`

    Example:
        >>> add_project_observation(24237, 1234, access_token)

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/add_project_observation.json
                :language: JSON

    Returns:
        Information about the added project observation
    """
    response = post_v1(
        'project_observations',
        access_token=access_token,
        json={'observation_id': observation_id, 'project_id': project_id},
        **params,
    )
    return response.json()


# TODO: This may not yet be working as intended
@document_request_params(docs._project_observation_params)
def delete_project_observation(
    project_id: int, observation_id: int, access_token: str = None, **params
):
    """Remove an observation from a project

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * API reference: :v1:`DELETE /projects/{id}/remove <Projects/delete_projects_id_remove>`
    * API reference: :v1:`DELETE /project_observations <Project_Observations/delete_project_observations_id>`

    Example:

        >>> delete_project_observation(24237, 1234, access_token)
    """
    return delete_v1(
        f'projects/{project_id}/remove',
        access_token=access_token,
        json={'observation_id': observation_id},
        **params,
    )
    # This version takes a separate 'project observation' ID (from association table?)
    # delete_v1(
    #     'project_observations',
    #     access_token=access_token,
    #     json={'observation_id': observation_id, 'project_id': project_id},
    #     **params,
    # )
