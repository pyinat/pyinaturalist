from typing import Dict, List

from pyinaturalist.constants import HistogramResponse, ListResponse
from pyinaturalist.controllers import BaseController
from pyinaturalist.docs import document_controller_params
from pyinaturalist.models import LifeList, Observation, Taxon, User
from pyinaturalist.models.taxon import TaxonCounts
from pyinaturalist.v1 import (
    create_observation,
    delete_observation,
    get_observation_histogram,
    get_observation_identifiers,
    get_observation_observers,
    get_observation_species_counts,
    get_observation_taxonomy,
    get_observations,
    upload,
)


# TODO: Fix type checking for return types
class ObservationController(BaseController):
    """Controller for observation requests"""

    @document_controller_params(get_observations)
    def search(self, **params) -> List[Observation]:
        response = get_observations(**params, **self.client.settings)
        return Observation.from_json_list(response)  # type: ignore

    # TODO: Does this need a model with utility functions, or is {datetime: count} sufficient?
    @document_controller_params(get_observation_histogram)
    def histogram(self, **params) -> HistogramResponse:
        return get_observation_histogram(**params, **self.client.settings)

    @document_controller_params(get_observation_identifiers)
    def identifiers(self, **params) -> Dict[int, User]:
        response = get_observation_identifiers(**params, **self.client.settings)
        return {r['count']: User.from_json(r['user']) for r in response['results']}  # type: ignore

    @document_controller_params(get_observation_taxonomy, add_common_args=False)
    def life_list(self, *args, **params) -> LifeList:
        response = get_observation_taxonomy(*args, **params, **self.client.settings)
        return LifeList.from_json(response.json())  # type: ignore

    # TODO: Separate model for these results? (maybe a User subclass)
    # TODO: Include species_counts
    @document_controller_params(get_observation_observers)
    def observers(self, **params) -> Dict[int, User]:
        response = get_observation_observers(**params, **self.client.settings)
        return {r['count']: User.from_json(r['user']) for r in response['results']}  # type: ignore

    @document_controller_params(get_observation_species_counts)
    def species_counts(self, **params) -> Dict[int, Taxon]:
        response = get_observation_species_counts(**params, **self.client.settings)
        return TaxonCounts.from_json(response)  # type: ignore

    # TODO: create observations with Observation objects
    def _create(self, *observations: Observation, **params):
        for obs in observations:
            create_observation(obs.to_json(), **params, **self.client.settings)

    @document_controller_params(delete_observation)
    def delete(self, *observation_ids: int, **params):
        for obs_id in observation_ids:
            delete_observation(obs_id, **params, **self.client.settings)

    # TODO: Add model for sound files, return list of model objects
    @document_controller_params(upload)
    def upload(self, **params) -> ListResponse:
        return upload(**params, **self.client.settings)
