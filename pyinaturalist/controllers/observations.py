from pyinaturalist.constants import HistogramResponse, IntOrStr, ListResponse
from pyinaturalist.controllers import BaseController
from pyinaturalist.docs import document_controller_params
from pyinaturalist.models import LifeList, Observation, TaxonCounts, TaxonSummary, UserCounts
from pyinaturalist.paginator import Paginator
from pyinaturalist.v1 import (
    create_observation,
    delete_observation,
    get_observation_histogram,
    get_observation_identifiers,
    get_observation_observers,
    get_observation_species_counts,
    get_observation_taxon_summary,
    get_observation_taxonomy,
    get_observations,
    update_observation,
    upload,
)


class ObservationController(BaseController):
    """:fa:`binoculars` Controller for Observation requests"""

    def from_id(self, *observation_ids, **params) -> Paginator[Observation]:
        """Get observations by ID

        Args:
            observation_ids: One or more observation IDs
        """
        return self.client.paginate(get_observations, Observation, id=observation_ids, **params)

    @document_controller_params(get_observations)
    def search(self, **params) -> Paginator[Observation]:
        return self.client.paginate(get_observations, Observation, method='id', **params)

    # TODO: Does this need a model with utility functions, or is {datetime: count} sufficient?
    @document_controller_params(get_observation_histogram)
    def histogram(self, **params) -> HistogramResponse:
        return self.client.request(get_observation_histogram, **params)

    @document_controller_params(get_observation_identifiers)
    def identifiers(self, **params) -> UserCounts:
        response = self.client.request(get_observation_identifiers, **params)
        return UserCounts.from_json(response)

    @document_controller_params(get_observation_observers)
    def observers(self, **params) -> UserCounts:
        response = self.client.request(get_observation_observers, **params)
        return UserCounts.from_json(response)

    @document_controller_params(get_observation_taxonomy, add_common_args=False)
    def life_list(self, user_id: IntOrStr, **params) -> LifeList:
        response = self.client.request(get_observation_taxonomy, user_id=user_id, **params)
        return LifeList.from_json(response)

    @document_controller_params(get_observation_species_counts)
    def species_counts(self, **params) -> TaxonCounts:
        response = self.client.request(get_observation_species_counts, **params)
        return TaxonCounts.from_json(response)

    @document_controller_params(get_observation_taxon_summary)
    def taxon_summary(self, observation_id: int, **params) -> TaxonSummary:
        response = self.client.request(
            get_observation_taxon_summary, observation_id=observation_id, **params
        )
        return TaxonSummary.from_json(response)

    # TODO: create observations with Observation objects; requires model updates
    @document_controller_params(create_observation)
    def create(self, **params) -> Observation:
        response = self.client.request(create_observation, auth=True, **params)
        return Observation.from_json(response)

    def delete(self, *observation_ids: int, **params):
        """Delete observations

        Args:
            observation_ids: One or more observation IDs
        """
        for observation_id in observation_ids:
            self.client.request(
                delete_observation,
                auth=True,
                observation_id=observation_id,
                **params,
            )

    @document_controller_params(update_observation)
    def update(self, **params) -> Observation:
        response = self.client.request(update_observation, auth=True, **params)
        return Observation.from_json(response)

    # TODO: Add model for sound files, return list of model objects
    @document_controller_params(upload)
    def upload(self, **params) -> ListResponse:
        return self.client.request(upload, auth=True, **params)
