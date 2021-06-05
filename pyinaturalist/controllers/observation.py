from typing import List

from pyinaturalist.controllers import BaseController
from pyinaturalist.models import Observation
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

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    # TODO: Use forge to reuse function signatures
    # TODO: Support passing session to all API functions
    def search(self, *args, **kwargs) -> List[Observation]:
        """Wrapper for :py:func:`.v1.get_observations()`"""
        results = get_observations(*args, **kwargs, session=self.session)
        return Observation.from_json_list(results)
