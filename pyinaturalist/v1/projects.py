from pyinaturalist.constants import PROJECT_ORDER_BY_PROPERTIES, IntOrStr, JsonResponse, MultiInt
from pyinaturalist.converters import convert_all_coordinates, convert_all_timestamps, ensure_list
from pyinaturalist.docs import document_request_params
from pyinaturalist.docs import templates as docs
from pyinaturalist.paginator import paginate_all
from pyinaturalist.request_params import split_common_params, validate_multiple_choice_param
from pyinaturalist.v1 import delete_v1, get_v1, post_v1, put_v1


@document_request_params(docs._projects_params, docs._pagination)
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
    if params.get('page') == 'all':
        projects = paginate_all(get_v1, 'projects', **params)
    else:
        projects = get_v1('projects', **params).json()

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
    response = get_v1(
        'projects', rule_details=rule_details, ids=project_id, allow_str_ids=True, **params
    )

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


def add_project_users(project_id: IntOrStr, user_ids: MultiInt, **params):
    """Add users to project observation rules

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * This only affects observation rules, **not** project membership

    Args:
        project_id: Either numeric project ID or URL slug
        user_ids: One or more user IDs to add. Only accepts numeric IDs.
    """
    rules = _get_project_rules(project_id)
    for user_id in ensure_list(user_ids):
        rules.append(
            {'operand_id': user_id, 'operand_type': 'User', 'operator': 'observed_by_user?'}
        )

    return update_project(project_id, project_observation_rules_attributes=rules, **params)


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

        >>> delete_project_observation(24237, 1234, access_token=access_token)
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


def delete_project_users(project_id: IntOrStr, user_ids: MultiInt, **params):
    """Remove users from project observation rules

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * This only affects observation rules, **not** project membership

    Args:
        project_id: Either numeric project ID or URL slug
        user_ids: One or more user IDs to remove. Only accepts numeric IDs.
    """
    rules = _get_project_rules(project_id)
    str_user_ids = [str(user_id) for user_id in ensure_list(user_ids)]
    for rule in rules:
        if rule['operand_type'] == 'User' and str(rule['operand_id']) in str_user_ids:
            rule['_destroy'] = True

    return update_project(project_id, project_observation_rules_attributes=rules, **params)


# TODO: Support image uploads for `cover` and `icon`
@document_request_params(docs._project_update_params)
def update_project(project_id: IntOrStr, **params):
    """Update a project

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * Undocumented endpoint; may be subject to braking changes in the future
    * ``admin_attributes`` and ``project_observation_rules_attributes`` each accept a list of dicts
      in the formats shown below. These can be obtained from :py:func:`get_projects`, modified, and
      then passed to this function::

        {
            "admin_attributes": [
                {"id": int, "role": str, "user_id": int, "_destroy": bool},
            ],
            "project_observation_rules_attributes": [
                {"operator": str, "operand_type": str, "operand_id": int, "id": int, "_destroy": bool},
            ],
        }

    Example:

        >>> update_project(
        ...     'api-test-project',
        ...     title='Test Project',
        ...     description='This is a test project',
        ...     prefers_rule_native=True,
        ...     access_token=access_token,
        ... )

    """
    # Split API request params from common function args
    params, kwargs = split_common_params(params)
    kwargs['timeout'] = kwargs.get('timeout') or 60  # This endpoint can be a bit slow

    response = put_v1(
        f'projects/{project_id}',
        json={'project': params},
        **kwargs,
    )
    return response.json()


# TODO: bypass cache for this call?
def _get_project_rules(project_id):
    project = get_projects_by_id(project_id)['results'][0]
    return project.get('project_observation_rules', [])
