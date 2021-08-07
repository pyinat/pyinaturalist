from typing import List

from pyinaturalist.constants import ListResponse
from pyinaturalist.controllers import BaseController
from pyinaturalist.docs import document_controller_params
from pyinaturalist.models import Project
from pyinaturalist.v1 import add_project_observation, get_projects, get_projects_by_id


class ProjectController(BaseController):
    """:fa:`users` Controller for project requests"""

    def from_id(self, *project_ids, **params) -> List[Project]:
        """Get projects by ID

        Args:
            project_ids: One or more project IDs
        """
        response = self.client.request(get_projects_by_id, project_id=project_ids, **params)
        return Project.from_json_list(response)

    @document_controller_params(get_projects)
    def search(self, **params) -> List[Project]:
        response = self.client.request(get_projects, **params)
        return Project.from_json_list(response)

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
