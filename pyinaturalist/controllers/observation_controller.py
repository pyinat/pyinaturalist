from typing import Optional

from pyinaturalist.constants import (
    API_V1,
    V1_OBS_ORDER_BY_PROPERTIES,
    HistogramResponse,
    IntOrStr,
    ListResponse,
)
from pyinaturalist.controllers import BaseController
from pyinaturalist.docs import document_controller_params
from pyinaturalist.models import (
    ControlledTermCounts,
    LifeList,
    Observation,
    TaxonCounts,
    TaxonSummary,
    UserCounts,
)
from pyinaturalist.paginator import IDRangePaginator, Paginator
from pyinaturalist.request_params import validate_multiple_choice_param
from pyinaturalist.v1 import (
    create_observation,
    delete_observation,
    get_observation_histogram,
    get_observation_identifiers,
    get_observation_observers,
    get_observation_popular_field_values,
    get_observation_species_counts,
    get_observation_taxon_summary,
    get_observation_taxonomy,
    get_observations,
    update_observation,
    upload,
)


class ObservationController(BaseController):
    """:fa:`binoculars` Controller for Observation requests"""

    def __call__(self, observation_id, **kwargs) -> Optional[Observation]:
        """Get a single observation by ID"""
        return self.from_ids(observation_id, **kwargs).one()

    def from_ids(self, *observation_ids, **params) -> Paginator[Observation]:
        """Get observations by ID

        Args:
            observation_ids: One or more observation IDs
        """
        return self.client.paginate(get_observations, Observation, id=observation_ids, **params)

    @document_controller_params(get_observations)
    def search(self, **params) -> Paginator[Observation]:
        # Using a simplified version of v1.get_observations() to avoid duplicate conversions
        def _get_observations(**params):
            params = validate_multiple_choice_param(params, 'order_by', V1_OBS_ORDER_BY_PROPERTIES)
            return self.client.session.get(f'{API_V1}/observations', **params).json()

        return self.client.paginate(_get_observations, Observation, cls=IDRangePaginator, **params)

    # TODO: Does this need a model with utility functions, or is {datetime: count} sufficient?
    @document_controller_params(get_observation_histogram)
    def histogram(self, **params) -> HistogramResponse:
        return self.client.request(get_observation_histogram, **params)

    @document_controller_params(get_observation_identifiers)
    def identifiers(self, **params) -> UserCounts:
        response = self.client.request(get_observation_identifiers, **params)
        return UserCounts.from_json(response)

    @document_controller_params(get_observation_taxonomy, add_common_args=False)
    def life_list(self, user_id: IntOrStr, **params) -> LifeList:
        response = self.client.request(get_observation_taxonomy, user_id=user_id, **params)
        return LifeList.from_json(response)

    @document_controller_params(get_observation_observers)
    def observers(self, **params) -> UserCounts:
        response = self.client.request(get_observation_observers, **params)
        return UserCounts.from_json(response)

    @document_controller_params(get_observation_popular_field_values)
    def popular_fields(self, **params) -> ControlledTermCounts:
        response = self.client.request(get_observation_popular_field_values, **params)
        return ControlledTermCounts.from_json(response)

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
