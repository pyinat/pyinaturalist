from typing import List

from pyinaturalist.constants import HistogramResponse, ListResponse
from pyinaturalist.controllers import BaseController
from pyinaturalist.docs import document_controller_params
from pyinaturalist.models import LifeList, Observation, TaxonCounts, TaxonSummary, UserCounts
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
    upload,
)


# TODO: Batch from_id requests if max GET URL length is exceeded
# TODO: Consistent naming for /{id} requests. from_id(), id(), by_id(), other?
class ObservationController(BaseController):
    """:fa:`binoculars` Controller for observation requests"""

    def from_id(self, *observation_ids, **params) -> List[Observation]:
        """Get observations by ID

        Args:
            observation_ids: One or more observation IDs
        """
        response = self.client.request(get_observations, id=observation_ids, **params)
        return Observation.from_json_list(response)

    @document_controller_params(get_observations)
    def search(self, **params) -> List[Observation]:
        response = self.client.request(get_observations, **params)
        return Observation.from_json_list(response)

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
    def life_list(self, *args, **params) -> LifeList:
        response = self.client.request(get_observation_taxonomy, *args, **params)
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

    # TODO: Add model for sound files, return list of model objects
    @document_controller_params(upload)
    def upload(self, **params) -> ListResponse:
        return self.client.request(upload, auth=True, **params)