from pyinaturalist.constants import IntOrStr, ListResponse, MultiInt, MultiIntOrStr
from pyinaturalist.controllers import BaseController
from pyinaturalist.converters import ensure_list
from pyinaturalist.docs import copy_doc_signature
from pyinaturalist.docs import templates as docs
from pyinaturalist.models import Project
from pyinaturalist.paginator import Paginator
from pyinaturalist.v1 import (
    add_project_observation,
    add_project_users,
    delete_project_users,
    get_projects,
    get_projects_by_id,
    update_project,
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

    def from_ids(self, project_ids: MultiIntOrStr, **params) -> Paginator[Project]:
        """Get projects by ID

        Example:
            >>> client.projects.from_id([1234, 5678])

        Args:
            project_ids: One or more project IDs
        """
        return self.client.paginate(get_projects_by_id, Project, project_id=project_ids, **params)

    @copy_doc_signature(docs._projects_params)
    def search(self, **params) -> Paginator[Project]:
        """Search projects

        .. rubric:: Notes

        * API reference: :v1:`GET /projects <Projects/get_projects>`

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
        return self.client.paginate(get_projects, Project, **params)

    def add_observations(
        self, project_id: int, observation_ids: MultiInt, **params
    ) -> ListResponse:
        """Add an observation to a project

        .. rubric:: Notes

        * :fa:`lock` :ref:`Requires authentication <auth>`
        * API reference: :v1:`POST projects/{id}/add <Projects/post_projects_id_add>`
        * API reference: :v1:`POST /project_observations <Project_Observations/post_project_observations>`

        Example:
            >>> client.projects.add_observations(24237, 1234)

        Args:
            project_id: ID of project to add onto
            observation_ids: One or more observation IDs to add
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
