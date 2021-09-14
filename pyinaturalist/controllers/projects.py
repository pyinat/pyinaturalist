from pyinaturalist.constants import ListResponse
from pyinaturalist.controllers import BaseController
from pyinaturalist.docs import document_controller_params
from pyinaturalist.models import Project
from pyinaturalist.paginator import Paginator
from pyinaturalist.v1 import add_project_observation, get_projects, get_projects_by_id


class ProjectController(BaseController):
    """:fa:`users` Controller for Project requests"""

    def from_id(self, *project_ids, **params) -> Paginator[Project]:
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
