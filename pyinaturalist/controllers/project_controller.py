from typing import Optional

from pyinaturalist.constants import IntOrStr, ListResponse
from pyinaturalist.controllers import BaseController
from pyinaturalist.docs import document_controller_params
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

    def __call__(self, project_id, **kwargs) -> Optional[Project]:
        """Get a single project by ID"""
        return self.from_ids(project_id, **kwargs).one()

    def from_ids(self, *project_ids: IntOrStr, **params) -> Paginator[Project]:
        """Get projects by ID

        Args:
            project_ids: One or more project IDs
        """
        return self.client.paginate(get_projects_by_id, Project, project_id=project_ids, **params)

    @document_controller_params(get_projects)
    def search(self, **params) -> Paginator[Project]:
        return self.client.paginate(get_projects, Project, **params)

    def add_observations(self, project_id: int, *observation_ids: int, **params) -> ListResponse:
        """Add an observation to a project

        Args:
            project_id: ID of project to add onto
            observation_ids: One or more observation IDs to add
        """
        responses = []
        for observation_id in observation_ids:
            response = self.client.request(
                add_project_observation,
                project_id=project_id,
                observation_id=observation_id,
                auth=True,
                **params
            )
            responses.append(response)
        return responses

    @document_controller_params(update_project)
    def update(self, project_id: IntOrStr, **params) -> Project:
        response = self.client.request(update_project, project_id, **params)
        return Project.from_json(response)

    @document_controller_params(add_project_users)
    def add_users(self, project_id: IntOrStr, *user_ids: int, **params) -> Project:
        response = self.client.request(add_project_users, project_id, user_ids, **params)
        return Project.from_json(response)

    @document_controller_params(delete_project_users)
    def delete_users(self, project_id: IntOrStr, *user_ids: int, **params) -> Project:
        response = self.client.request(delete_project_users, project_id, user_ids, **params)
        return Project.from_json(response)
