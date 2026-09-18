from copy import deepcopy

from pyinaturalist.client import delete, get, paginate_all, post
from pyinaturalist.constants import (
    API_V2,
    PROJECT_ORDER_BY_PROPERTIES,
    IntOrStr,
    JsonResponse,
    MultiInt,
    RequestParams,
    ResponseResult,
)
from pyinaturalist.converters import convert_all_coordinates, convert_all_timestamps, ensure_list
from pyinaturalist.docs import document_request_params
from pyinaturalist.docs import templates as docs
from pyinaturalist.exceptions import ObservationNotFound
from pyinaturalist.request_params import validate_multiple_choice_param
from pyinaturalist.v2.observations import get_observations


@document_request_params(docs._projects_params, docs._observation_v2, docs._pagination)
def get_projects(**params) -> JsonResponse:
    """Search projects

    .. rubric:: Notes

    * API reference: :v2:`GET /projects <Projects/get_projects>`
    * See `iNaturalist API v2 documentation <https://api.inaturalist.org/v2/docs>`_ for details on
      selecting return fields using ``fields`` parameter
    * The v2 API only accepts ``'collection'`` and ``'umbrella'`` for the ``type`` parameter

    Example:
        Search for projects about invasive species within 400km of Vancouver, BC:

        >>> response = get_projects(
        >>>     q='invasive',
        >>>     lat=49.27,
        >>>     lng=-123.08,
        >>>     radius=400,
        >>>     order_by='distance',
        >>>     fields='all',
        >>> )

        Show basic info for projects in response:

        >>> pprint(response)
        [8291    ] PNW Invasive Plant EDDR
        [19200   ] King County (WA) Noxious and Invasive Weeds
        [102925  ] Keechelus/Kachess Invasive Plants
        ...

        .. dropdown:: Example Response (default/minimal)
            :color: primary
            :icon: code-square

            .. literalinclude:: ../sample_data/v2/get_projects_minimal.json
                :language: JSON

        .. dropdown:: Example Response (all fields)
            :color: primary
            :icon: code-square

            .. literalinclude:: ../sample_data/v2/get_projects_by_id.json
                :language: JSON

    Returns:
        Response dict containing project records
    """
    params = validate_multiple_choice_param(params, 'order_by', PROJECT_ORDER_BY_PROPERTIES)
    params = _convert_fields(params)

    if params.get('fields') not in ['all', None]:
        projects = _get_post_projects(params)
    else:
        projects = _get_projects(params)

    projects['results'] = convert_all_coordinates(projects['results'])
    projects['results'] = convert_all_timestamps(projects['results'])
    return projects


def get_projects_by_id(
    project_id: MultiInt,
    rule_details: bool | None = None,
    **params,
) -> JsonResponse:
    """Get one or more projects by ID

    .. rubric:: Notes

    * API reference: :v2:`GET /projects/{id} <Projects/get_projects_id>`
    * Unlike the v1 API, the v2 API only accepts numeric project IDs (not URL slugs)

    Example:
        >>> response = get_projects_by_id([8348, 6432], fields='all')
        >>> pprint(response)
        [8348] Tucson High Native and Invasive Species Inventory
        [6432] CBWN Invasive Plants

        .. dropdown:: Example Response (all fields)
            :color: primary
            :icon: code-square

            .. literalinclude:: ../sample_data/v2/get_projects_by_id.json
                :language: JSON

    Args:
        project_id: Get projects with this ID. Multiple values are allowed.
        rule_details: Return more information about project rules, for example return a full taxon
            object instead of simply an ID

    Returns:
        Response dict containing project records
    """
    params['rule_details'] = rule_details
    params = _convert_fields(params)

    n_ids = len(ensure_list(project_id))
    if params.get('fields') not in ['all', None] or n_ids > 30:
        body = dict(params)
        body['id'] = project_id
        query_params = {k: body.pop(k) for k in ['page', 'per_page'] if k in body}
        headers = {'X-HTTP-Method-Override': 'GET'}
        projects = post(f'{API_V2}/projects', headers=headers, json=body, **query_params).json()
    else:
        projects = get(f'{API_V2}/projects', ids=project_id, **params).json()

    projects['results'] = convert_all_coordinates(projects['results'])
    projects['results'] = convert_all_timestamps(projects['results'])
    return projects


@document_request_params(docs._access_token)
def add_project_observation(project_id: int, observation_id: IntOrStr, **params) -> JsonResponse:
    """Add an observation to a project

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * API reference: :v2:`POST /project_observations <ProjectObservations/post_project_observations>`
    * This only applies to traditional projects. Collection and umbrella projects include
      observations based on their rules, and cannot have observations added manually.
    * The v2 API identifies observations by UUID. If a numeric observation ID is provided, an extra
      request will be made to look up its UUID.

    Example:
        >>> add_project_observation(24237, '53411fc2-bdf0-434e-afce-4dac33970173', access_token=token)

    Args:
        project_id: ID of project to add onto
        observation_id: ID or UUID of observation to add

    Returns:
        Response dict containing the newly created project observation record
    """
    if not isinstance(observation_id, str):
        observation = _get_observation(observation_id, fields={'uuid': True}, **params)
        observation_id = observation['uuid']

    body = {'project_observation': {'project_id': project_id, 'observation_id': observation_id}}
    response = post(f'{API_V2}/project_observations', json=body, **params)
    return response.json()


@document_request_params(docs._access_token)
def delete_project_observation(project_id: int, observation_id: IntOrStr, **params):
    """Remove an observation from a project

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * API reference: :v2:`DELETE /project_observations/{uuid} <ProjectObservations/delete_project_observations_uuid>`
    * This only applies to traditional projects. Collection and umbrella projects include
      observations based on their rules, and cannot have observations removed manually.
    * This endpoint requires the UUID of the *project observation* record (not the observation
      itself), so an extra request will be made to look it up.

    Example:
        >>> delete_project_observation(24237, '53411fc2-bdf0-434e-afce-4dac33970173', access_token=token)

    Args:
        project_id: ID of project to remove from
        observation_id: ID or UUID of observation to remove

    Returns:
        If successful, no response is returned from this endpoint

    Raises:
        :py:exc:`.ObservationNotFound` if the requested observation doesn't exist
        :py:exc:`ValueError` if the observation is not in the specified project
    """
    fields = {'project_observations': {'uuid': True, 'project': {'id': True}}}
    observation = _get_observation(observation_id, fields=fields, **params)
    project_observations = [
        po
        for po in observation.get('project_observations', [])
        if po['project']['id'] == project_id
    ]
    if not project_observations:
        raise ValueError(f'Observation {observation_id} is not in project {project_id}')

    delete(f'{API_V2}/project_observations/{project_observations[0]["uuid"]}', **params)


def _get_observation(observation_id: IntOrStr, fields: dict, **params) -> ResponseResult:
    """Get a single observation by either numeric ID or UUID, with the specified return fields"""
    id_param = (
        {'uuid': observation_id} if isinstance(observation_id, str) else {'id': observation_id}
    )
    response = get_observations(**id_param, fields=fields, **params)
    if not response['results']:
        raise ObservationNotFound(f'Observation not found: {observation_id}')
    return response['results'][0]


def _convert_fields(params: RequestParams) -> RequestParams:
    """Convert ``except_fields`` into an equivalent ``fields`` value, if specified"""
    except_fields = params.pop('except_fields', None)

    if params.get('fields') and except_fields:
        raise ValueError('Cannot use both fields and except_fields')

    # Request all fields except those specified
    if except_fields:
        params['fields'] = deepcopy(ALL_PROJECT_FIELDS)
        for k in except_fields:
            params['fields'].pop(k, None)

    return params


def _get_projects(params: RequestParams) -> JsonResponse:
    if params.get('page') == 'all':
        return paginate_all(get, f'{API_V2}/projects', **params)
    else:
        return get(f'{API_V2}/projects', **params).json()


def _get_post_projects(params: RequestParams) -> JsonResponse:
    """Use POST method to get projects with selection of return fields."""
    headers = {'X-HTTP-Method-Override': 'GET'}
    body = params
    query_params = {k: body.pop(k) for k in ['page', 'per_page'] if k in body}
    if query_params.get('page') == 'all':
        return paginate_all(
            post,
            f'{API_V2}/projects',
            headers=headers,
            json=body,
            **query_params,
        )
    else:
        return post(f'{API_V2}/projects', headers=headers, json=body, **query_params).json()


# Minimal user fields to include in nested user records
_USER_FIELDS = {
    'id': True,
    'icon_url': True,
    'login': True,
    'name': True,
    'observations_count': True,
}

# The full `fields` value to request all project details
ALL_PROJECT_FIELDS = {
    'admins': {
        'id': True,
        'project_id': True,
        'role': True,
        'user': _USER_FIELDS,
        'user_id': True,
    },
    'banner_color': True,
    'created_at': True,
    'delegated_project_id': True,
    'description': True,
    'flags': {
        'comment': True,
        'created_at': True,
        'flag': True,
        'id': True,
        'resolved': True,
        'resolved_at': True,
        'updated_at': True,
        'user': _USER_FIELDS,
        'user_id': True,
    },
    'header_image_contain': True,
    'header_image_file_name': True,
    'header_image_url': True,
    'hide_title': True,
    'hide_umbrella_map_flags': True,
    'icon': True,
    'icon_file_name': True,
    'id': True,
    'is_delegated_umbrella': True,
    'is_umbrella': True,
    'latitude': True,
    'location': True,
    'longitude': True,
    'observation_requirements_updated_at': True,
    'place_id': True,
    'prefers_user_trust': True,
    'project_observation_fields': {
        'id': True,
        'observation_field': {
            'allowed_values': True,
            'datatype': True,
            'description': True,
            'id': True,
            'name': True,
            'users_count': True,
            'uuid': True,
            'values_count': True,
        },
        'position': True,
        'required': True,
    },
    'project_observation_rules': {
        'id': True,
        'operand_id': True,
        'operand_type': True,
        'operator': True,
        'place': {'id': True, 'name': True, 'display_name': True, 'place_type': True},
        'project': {'id': True, 'title': True, 'slug': True},
        'taxon': {
            'id': True,
            'name': True,
            'preferred_common_name': True,
            'rank': True,
            'iconic_taxon_name': True,
        },
        'user': _USER_FIELDS,
    },
    'project_type': True,
    'rule_preferences': {'field': True, 'value': True},
    'search_parameters': {
        'field': True,
        'value': True,
        'value_bool': True,
        'value_date': True,
        'value_keyword': True,
        'value_number': True,
    },
    'site_features': {'featured_at': True, 'noteworthy': True, 'site_id': True},
    'slug': True,
    'terms': True,
    'title': True,
    'updated_at': True,
    'user': _USER_FIELDS,
    'user_id': True,
    'user_ids': True,
}
