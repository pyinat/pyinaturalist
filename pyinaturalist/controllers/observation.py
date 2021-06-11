# TODO: Just copying code from original API functions for now; will figure out the best means of code reuse later
# TODO: Update examples and example responses
from typing import Dict, List

from pyinaturalist import api_docs as docs
from pyinaturalist.constants import API_V1_BASE_URL, NODE_OBS_ORDER_BY_PROPERTIES
from pyinaturalist.controllers import BaseController
from pyinaturalist.forge_utils import document_request_params
from pyinaturalist.models import Observation, Taxon, User
from pyinaturalist.pagination import add_paginate_all
from pyinaturalist.request_params import validate_multiple_choice_param


class ObservationController(BaseController):
    """Controller for observation requests"""

    @document_request_params([*docs._get_observations, docs._pagination, docs._only_id])
    @add_paginate_all(method='id')
    def search(self, **params) -> List[Observation]:
        """Search observations.

        **API reference:** http://api.inaturalist.org/v1/docs/#!/Observations/get_observations

        Example:

            Get observations of Monarch butterflies with photos + public location info,
            on a specific date in the provice of Saskatchewan, CA (place ID 7953):

            >>> response = get_observations(
            >>>     taxon_name='Danaus plexippus',
            >>>     created_on='2020-08-27',
            >>>     photos=True,
            >>>     geo=True,
            >>>     geoprivacy='open',
            >>>     place_id=7953,
            >>> )

            Get basic info for observations in response:

            >>> from pyinaturalist.formatters import format_observations
            >>> print(format_observations(response))
            '[57754375] Species: Danaus plexippus (Monarch) observed by samroom on 2020-08-27 at Railway Ave, Wilcox, SK'
            '[57707611] Species: Danaus plexippus (Monarch) observed by ingridt3 on 2020-08-26 at Michener Dr, Regina, SK'

            .. admonition:: Example Response
                :class: toggle

                .. literalinclude:: ../sample_data/get_observations_node.py

        Returns:
            Response dict containing observation records
        """
        validate_multiple_choice_param(params, 'order_by', NODE_OBS_ORDER_BY_PROPERTIES)
        response = self.client.get(f'{API_V1_BASE_URL}/observations', params=params)
        return Observation.from_json_list(response.json())

    @document_request_params([*docs._get_observations, docs._pagination])
    def identifiers(self, **params) -> Dict[int, User]:
        """Get identifiers of observations matching the search criteria and the count of
        observations they have identified. By default, results are sorted by ID count in descending.

        **API reference:** https://api.inaturalist.org/v1/docs/#!/Observations/get_observations_identifiers

        Note: This endpoint will only return up to 500 results.

        Example:
            >>> response = get_observation_identifiers(place_id=72645)
            >>> print(format_users(response, align=True))
            [409010  ] jdoe42 (Jane Doe)
            [691216  ] jbrown252 (James Brown)
            [3959037 ] tnsparkleberry

            .. admonition:: Example Response
                :class: toggle

                .. literalinclude:: ../sample_data/get_observation_identifiers_ex_results.json
                    :language: JSON

        Returns:
            Response dict of identifiers
        """
        params.setdefault('per_page', 500)
        response = self.client.get(f'{API_V1_BASE_URL}/observations/identifiers', params=params)
        results = response.json()['results']

        return {r['count']: User.from_json(r['user']) for r in results}

    # TODO: Separate model for these results? (maybe a User subclass)
    # TODO: Include species_counts
    @document_request_params([*docs._get_observations, docs._pagination])
    def observers(self, **params) -> Dict[int, User]:
        """Get observers of observations matching the search criteria and the count of
        observations and distinct taxa of rank species they have observed.

        Notes:
            * Options for ``order_by`` are 'observation_count' (default) or 'species_count'
            * This endpoint will only return up to 500 results
            * See this issue for more details: https://github.com/inaturalist/iNaturalistAPI/issues/235

        **API reference:** https://api.inaturalist.org/v1/docs/#!/Observations/get_observations_observers

        Example:
            >>> response = get_observation_observers(place_id=72645, order_by='species_count')
            >>> print(format_users(response, align=True))
            [1566366 ] fossa1211
            [674557  ] schurchin
            [5813    ] fluffberger (Fluff Berger)


            .. admonition:: Example Response
                :class: toggle

                .. literalinclude:: ../sample_data/get_observation_observers_ex_results.json
                    :language: JSON

        Returns:
            Response dict of observers
        """
        params.setdefault('per_page', 500)
        response = self.client.get(f'{API_V1_BASE_URL}/observations/observers', params=params)
        results = response.json()['results']
        return {r['observation_count']: User.from_json(r['user']) for r in results}

    @document_request_params([*docs._get_observations, docs._pagination])
    @add_paginate_all(method='page')
    def species_counts(self, **params) -> Dict[int, Taxon]:
        """Get all species (or other 'leaf taxa') associated with observations matching the search
        criteria, and the count of observations they are associated with.
        **Leaf taxa** are the leaves of the taxonomic tree, e.g., species, subspecies, variety, etc.

        **API reference:** https://api.inaturalist.org/v1/docs/#!/Observations/get_observations_species_counts

        Example:
            >>> response = get_observation_species_counts(user_login='my_username', quality_grade='research')
            >>> print(format_species_counts(response))
            [62060] Species: Palomena prasina (Green Shield Bug): 10
            [84804] Species: Graphosoma italicum (European Striped Shield Bug): 8
            [55727] Species: Cymbalaria muralis (Ivy-leaved toadflax): 3
            ...

            .. admonition:: Example Response
                :class: toggle

                .. literalinclude:: ../sample_data/get_observation_species_counts.py

        Returns:
            Response dict containing taxon records with counts
        """
        response = self.client.get(f'{API_V1_BASE_URL}/observations/species_counts', params=params)
        results = response.json()['results']
        return {r['count']: Taxon.from_json(r['taxon']) for r in results}
