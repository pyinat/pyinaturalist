from typing import List

from pyinaturalist.constants import HistogramResponse, ListResponse
from pyinaturalist.controllers import BaseController, authenticated
from pyinaturalist.docs import document_controller_params
from pyinaturalist.models import LifeList, Observation, TaxonCounts, UserCounts
from pyinaturalist.models.taxon_meta import TaxonSummary
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
        response = get_observations(id=observation_ids, **params, **self.client.settings)
        return Observation.from_json_list(response)

    @document_controller_params(get_observations)
    def search(self, **params) -> List[Observation]:
        response = get_observations(**params, **self.client.settings)
        return Observation.from_json_list(response)

    # TODO: Does this need a model with utility functions, or is {datetime: count} sufficient?
    @document_controller_params(get_observation_histogram)
    def histogram(self, **params) -> HistogramResponse:
        return get_observation_histogram(**params, **self.client.settings)

    @document_controller_params(get_observation_identifiers)
    def identifiers(self, **params) -> UserCounts:
        response = get_observation_identifiers(**params, **self.client.settings)
        return UserCounts.from_json(response)

    @document_controller_params(get_observation_observers)
    def observers(self, **params) -> UserCounts:
        response = get_observation_observers(**params, **self.client.settings)
        return UserCounts.from_json(response)

    @document_controller_params(get_observation_taxonomy, add_common_args=False)
    def life_list(self, *args, **params) -> LifeList:
        response = get_observation_taxonomy(*args, **params, **self.client.settings)
        return LifeList.from_json(response)

    @document_controller_params(get_observation_species_counts)
    def species_counts(self, **params) -> TaxonCounts:
        response = get_observation_species_counts(**params, **self.client.settings)
        return TaxonCounts.from_json(response)

    @document_controller_params(get_observation_taxon_summary)
    def taxon_summary(self, observation_id: int, **params) -> TaxonSummary:
        response = get_observation_taxon_summary(observation_id, **params)
        return TaxonSummary.from_json(response)

    @document_controller_params(create_observation)
    @authenticated
    def create(self, **params) -> Observation:
        response = create_observation(**params, **self.client.settings)
        return Observation.from_json(response)

    # TODO: create observations with Observation objects; requires model updates
    # @authenticated
    # def create(self, *observations: Observation, **params):
    #     for obs in observations:
    #         create_observation(obs.to_json(), **params, **self.client.settings)

    @authenticated
    def delete(self, *observation_ids: int, **params):
        """Delete observations

        Args:
            observation_ids: One or more observation IDs
        """
        for obs_id in observation_ids:
            delete_observation(obs_id, **params, **self.client.settings)

    # TODO: Add model for sound files, return list of model objects
    @document_controller_params(upload)
    @authenticated
    def upload(self, **params) -> ListResponse:
        return upload(**params, **self.client.settings)
