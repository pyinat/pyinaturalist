from logging import getLogger
from typing import Optional

from pyinaturalist.constants import (
    API_V1,
    PROJECT_ORDER_BY_PROPERTIES,
    IntOrStr,
    JsonResponse,
    MultiInt,
    MultiIntOrStr,
)
from pyinaturalist.converters import convert_all_coordinates, convert_all_timestamps, ensure_list
from pyinaturalist.docs import document_request_params
from pyinaturalist.docs import templates as docs
from pyinaturalist.paginator import paginate_all
from pyinaturalist.request_params import split_common_params, validate_multiple_choice_param
from pyinaturalist.session import delete, get, get_refresh_params, post, put

logger = getLogger(__name__)


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
        projects = paginate_all(get, f'{API_V1}/projects', **params)
    else:
        projects = get(f'{API_V1}/projects', **params).json()

    projects['results'] = convert_all_coordinates(projects['results'])
    projects['results'] = convert_all_timestamps(projects['results'])
    return projects


def get_projects_by_id(
    project_id: MultiIntOrStr,
    rule_details: Optional[bool] = None,
    force_refresh: bool = False,
    **params,
) -> JsonResponse:
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
        force_refresh: Force a refresh of the project record from the API, bypassing both the local
            and CDN caches

    Returns:
        Response dict containing project records
    """
    if force_refresh:
        params.update(get_refresh_params(f'/projects/{project_id}'))
    response = get(
        f'{API_V1}/projects',
        rule_details=rule_details,
        ids=project_id,
        allow_str_ids=True,
        **params,
    )

    projects = response.json()
    projects['results'] = convert_all_coordinates(projects['results'])
    projects['results'] = convert_all_timestamps(projects['results'])
    return projects


@document_request_params(docs._project_observation_params)
def add_project_observation(
    project_id: int, observation_id: int, access_token: Optional[str] = None, **params
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
    response = post(
        f'{API_V1}/project_observations',
        access_token=access_token,
        json={'observation_id': observation_id, 'project_id': project_id},
        **params,
    )
    return response.json()


def add_project_users(project_id: IntOrStr, user_ids: MultiInt, **params) -> JsonResponse:
    """Add users to project observation rules

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * This only affects observation rules, **not** project membership

    Args:
        project_id: Either numeric project ID or URL slug
        user_ids: One or more user IDs to add. Only accepts numeric IDs.

    Returns:
        The updated project record
    """
    rules = _get_project_rules(project_id)
    existing_user_ids = [rule['operand_id'] for rule in rules if rule['operand_type'] == 'User']
    for user_id in ensure_list(user_ids):
        if user_id not in existing_user_ids:
            rules.append(
                {'operand_id': user_id, 'operand_type': 'User', 'operator': 'observed_by_user?'}
            )
        else:
            logger.warning(f'User {user_id} is already in project rules for {project_id}')
    return update_project(project_id, project_observation_rules_attributes=rules, **params)


# TODO: This may not yet be working as intended
@document_request_params(docs._project_observation_params)
def delete_project_observation(
    project_id: int, observation_id: int, access_token: Optional[str] = None, **params
):
    """Remove an observation from a project

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * API reference: :v1:`DELETE /projects/{id}/remove <Projects/delete_projects_id_remove>`
    * API reference: :v1:`DELETE /project_observations <Project_Observations/delete_project_observations_id>`

    Example:

        >>> delete_project_observation(24237, 1234, access_token=access_token)
    """
    return delete(
        f'{API_V1}/projects/{project_id}/remove',
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


def delete_project_users(project_id: IntOrStr, user_ids: MultiInt, **params) -> JsonResponse:
    """Remove users from project observation rules

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * This only affects observation rules, **not** project membership

    Args:
        project_id: Either numeric project ID or URL slug
        user_ids: One or more user IDs to remove. Only accepts numeric IDs.

    Returns:
        The updated project record
    """
    # Get and modify existing rules
    rules = _get_project_rules(project_id)
    str_user_ids = [str(user_id) for user_id in ensure_list(user_ids)]
    for rule in rules:
        if rule['operand_type'] == 'User' and str(rule['operand_id']) in str_user_ids:
            rule['_destroy'] = True

    # Update project and validate results
    project = update_project(project_id, project_observation_rules_attributes=rules, **params)
    _validate_removed_users(project, user_ids)
    return project


@document_request_params(docs._project_update_params)
def update_project(project_id: IntOrStr, **params) -> JsonResponse:
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

    Returns:
        The updated project record
    """
    # Split API request params from common function args
    params, kwargs = split_common_params(params)
    kwargs['timeout'] = kwargs.get('timeout') or 60  # This endpoint can be a bit slow

    response = put(
        f'{API_V1}/projects/{project_id}',
        json={'project': params},
        **kwargs,
    )
    return response.json()


def _get_project_rules(project_id):
    """Get the current rules for a project"""
    response = get_projects_by_id(project_id, force_refresh=True)
    project = response['results'][0]
    return project.get('project_observation_rules', [])


def _validate_removed_users(project: JsonResponse, user_ids: MultiInt):
    """Validate that users have been removed from project observation rules"""
    updated_user_ids = [
        rule['operand_id']
        for rule in project.get('project_observation_rules', [])
        if rule['operand_type'] == 'User'
    ]

    failed_ids = set(updated_user_ids) & set(ensure_list(user_ids))
    if failed_ids:
        logger.warning(f'Failed to remove users {list(failed_ids)} from project {project["id"]}')
