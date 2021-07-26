# TODO: Just copying code from original API functions for now; will figure out the best means of code reuse later
# TODO: Update examples and example responses
# TODO: Don't override return signature
from typing import Dict, List

from pyinaturalist.constants import (
    API_V1_BASE_URL,
    NODE_OBS_ORDER_BY_PROPERTIES,
    HistogramResponse,
    IntOrStr,
)
from pyinaturalist.controllers import BaseController
from pyinaturalist.converters import convert_histogram
from pyinaturalist.docs import copy_doc_signature
from pyinaturalist.models import LifeList, Observation, Taxon, User
from pyinaturalist.pagination import add_paginate_all
from pyinaturalist.request_params import validate_multiple_choice_param
from pyinaturalist.v1 import (
    get_observation_histogram,
    get_observation_identifiers,
    get_observation_observers,
    get_observation_species_counts,
    get_observation_taxonomy,
    get_observations,
)


class ObservationController(BaseController):
    """Controller for observation requests"""

    @copy_doc_signature(get_observations)
    @add_paginate_all(method='id')
    def search(self, **params) -> List[Observation]:
        validate_multiple_choice_param(params, 'order_by', NODE_OBS_ORDER_BY_PROPERTIES)
        response = self.client.get(f'{API_V1_BASE_URL}/observations', params=params)
        return Observation.from_json_list(response.json())

    # TODO: Does this need a model with utility functions, or is {datetime: count} sufficient?
    @copy_doc_signature(get_observation_histogram)
    def histogram(self, **params) -> HistogramResponse:
        response = self.client.get(f'{API_V1_BASE_URL}/observations/histogram', params=params)
        return convert_histogram(response.json())

    @copy_doc_signature(get_observation_identifiers)
    def identifiers(self, **params) -> Dict[int, User]:
        params.setdefault('per_page', 500)
        response = self.client.get(f'{API_V1_BASE_URL}/observations/identifiers', params=params)
        results = response.json()['results']
        return {r['count']: User.from_json(r['user']) for r in results}

    @copy_doc_signature(get_observation_taxonomy, add_common_args=False)
    @add_paginate_all(method='page')
    def life_list(self, user_id: IntOrStr, **params) -> LifeList:
        response = self.client.get(
            f'{API_V1_BASE_URL}/observations/taxonomy',
            params={'user_id': user_id},
        )
        return LifeList.from_json(response.json())

    # TODO: Separate model for these results? (maybe a User subclass)
    # TODO: Include species_counts
    @copy_doc_signature(get_observation_observers)
    def observers(self, **params) -> Dict[int, User]:
        params.setdefault('per_page', 500)
        response = self.client.get(f'{API_V1_BASE_URL}/observations/observers', params=params)
        results = response.json()['results']
        return {r['observation_count']: User.from_json(r['user']) for r in results}

    @copy_doc_signature(get_observation_species_counts)
    @add_paginate_all(method='page')
    def species_counts(self, **params) -> Dict[int, Taxon]:
        response = self.client.get(f'{API_V1_BASE_URL}/observations/species_counts', params=params)
        results = response.json()['results']
        return {r['count']: Taxon.from_json(r['taxon']) for r in results}
