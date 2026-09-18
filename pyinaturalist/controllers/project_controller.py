from pyinaturalist.client import Paginator
from pyinaturalist.constants import IntOrStr, ListResponse, MultiInt, MultiIntOrStr
from pyinaturalist.controllers import BaseController
from pyinaturalist.converters import ensure_list
from pyinaturalist.docs import copy_doc_signature
from pyinaturalist.docs import templates as docs
from pyinaturalist.models import Project
from pyinaturalist.v1 import add_project_users, delete_project_users, update_project
from pyinaturalist.v2 import (
    add_project_observation,
    delete_project_observation,
    get_projects,
    get_projects_by_id,
)


class ProjectController(BaseController):
    """:fa:`users` Controller for Project requests"""

    def __call__(self, project_id: int, **kwargs) -> Project | None:
        """Get a single project by ID

        Example:
            >>> client.projects(1234)

        Args:
            project_id: A single project ID
        """
        return self.from_ids(project_id, **kwargs).one()

    def from_ids(self, project_ids: MultiInt, **params) -> Paginator[Project]:
        """Get projects by ID

        .. rubric:: Notes

        * :fas:`file-circle-plus` :ref:`Paginated endpoint <pagination>`
        * API reference: :v2:`GET /projects/{id} <Projects/get_projects_id>`
        * All fields are returned by default; use ``fields`` to request a subset

        Example:
            >>> client.projects.from_id([1234, 5678])

        Args:
            project_ids: One or more numeric project IDs
        """
        params.setdefault('fields', 'all')
        return self.client.paginate(get_projects_by_id, Project, project_id=project_ids, **params)

    @copy_doc_signature(docs._projects_params)
    def search(self, **params) -> Paginator[Project]:
        """Search projects

        .. rubric:: Notes

        * :fas:`file-circle-plus` :ref:`Paginated endpoint <pagination>`
        * API reference: :v2:`GET /projects <Projects/get_projects>`
        * All fields are returned by default; use ``fields`` to request a subset

        Example:
            Search for projects about invasive species within 400km of Vancouver, BC:

            >>> client.projects.search(
            >>>     q='invasive',
            >>>     lat=49.27,
            >>>     lng=-123.08,
            >>>     radius=400,
            >>>     order_by='distance',
            >>> )
        """
        params.setdefault('fields', 'all')
        return self.client.paginate(get_projects, Project, **params)

    def add_observations(
        self, project_id: int, observation_ids: MultiIntOrStr, **params
    ) -> ListResponse:
        """Add one or more observations to a project

        .. rubric:: Notes

        * :fa:`lock` :ref:`Requires authentication <auth>`
        * API reference: :v2:`POST /project_observations <ProjectObservations/post_project_observations>`
        * This only applies to traditional projects. Collection and umbrella projects include
          observations based on their rules, and cannot have observations added manually.
        * If numeric observation IDs are provided instead of UUIDs, an extra request will be made
          for each one to look up its UUID.

        Example:
            >>> client.projects.add_observations(24237, '53411fc2-bdf0-434e-afce-4dac33970173')

        Args:
            project_id: ID of project to add onto
            observation_ids: One or more observation IDs or UUIDs to add
        """
        responses = []
        for observation_id in ensure_list(observation_ids):
            response = self.client.request(
                add_project_observation,
                project_id=project_id,
                observation_id=observation_id,
                auth=True,
                **params,
            )
            responses.append(response)
        return responses

    def delete_observations(self, project_id: int, observation_ids: MultiIntOrStr, **params):
        """Remove one or more observations from a project

        .. rubric:: Notes

        * :fa:`lock` :ref:`Requires authentication <auth>`
        * API reference: :v2:`DELETE /project_observations/{uuid}
          <ProjectObservations/delete_project_observations_uuid>`
        * This only applies to traditional projects. Collection and umbrella projects include
          observations based on their rules, and cannot have observations removed manually.
        * An extra request will be made for each observation to look up its project observation
          record.

        Example:
            >>> client.projects.delete_observations(24237, '53411fc2-bdf0-434e-afce-4dac33970173')

        Args:
            project_id: ID of project to remove from
            observation_ids: One or more observation IDs or UUIDs to remove
        """
        for observation_id in ensure_list(observation_ids):
            self.client.request(
                delete_project_observation,
                project_id=project_id,
                observation_id=observation_id,
                auth=True,
                **params,
            )

    @copy_doc_signature(docs._project_update_params)
    def update(self, project_id: IntOrStr, **params) -> Project:
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

            >>> client.projects.update(
            ...     'api-test-project',
            ...     title='Test Project',
            ...     description='This is a test project',
            ...     prefers_rule_native=True,
            ...     access_token=access_token,
            ... )
        """
        response = self.client.request(update_project, project_id, auth=True, **params)
        return Project.from_json(response)

    def add_users(self, project_id: IntOrStr, user_ids: MultiInt, **params) -> Project:
        """Add users to project observation rules

        .. rubric:: Notes

        * :fa:`lock` :ref:`Requires authentication <auth>`
        * This only affects observation rules, **not** project membership

        Example:
            >>> client.projects.add_users(1234, [1234, 5678])

        Args:
            project_id: Either numeric project ID or URL slug
            user_ids: One or more user IDs to add. Only accepts numeric IDs.
        """
        response = self.client.request(add_project_users, project_id, user_ids, auth=True, **params)
        return Project.from_json(response)

    def delete_users(self, project_id: IntOrStr, user_ids: MultiInt, **params) -> Project:
        """Remove users from project observation rules

        .. rubric:: Notes

        * :fa:`lock` :ref:`Requires authentication <auth>`
        * This only affects observation rules, **not** project membership

        Example:
            >>> client.projects.delete_users(1234, [1234, 5678])

        Args:
            project_id: Either numeric project ID or URL slug
            user_ids: One or more user IDs to remove. Only accepts numeric IDs.
        """
        response = self.client.request(
            delete_project_users, project_id, user_ids, auth=True, **params
        )
        return Project.from_json(response)
