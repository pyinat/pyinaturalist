from typing import Optional

from pyinaturalist.constants import IntOrStr
from pyinaturalist.controllers import BaseController
from pyinaturalist.docs import document_controller_params
from pyinaturalist.models import Place
from pyinaturalist.paginator import AutocompletePaginator, Paginator
from pyinaturalist.v1 import get_places_autocomplete, get_places_by_id, get_places_nearby


class PlaceController(BaseController):
    """:fa:`location-dot` Controller for Place requests"""

    def __call__(self, place_id, **kwargs) -> Optional[Place]:
        """Get a single place by ID"""
        return self.from_ids(place_id, **kwargs).one()

    def from_ids(self, *place_ids: IntOrStr, **params) -> Paginator[Place]:
        """Get places by ID

        Args:
            place_ids: One or more place IDs
        """
        return self.client.paginate(get_places_by_id, Place, place_id=place_ids, **params)

    @document_controller_params(get_places_autocomplete)
    def autocomplete(self, q: Optional[str] = None, **params) -> Paginator[Place]:
        return self.client.paginate(
            get_places_autocomplete,
            Place,
            cls=AutocompletePaginator,
            q=q,
            per_page=20,
            **params,
        )

    @document_controller_params(get_places_nearby)
    def nearby(
        self, nelat: float, nelng: float, swlat: float, swlng: float, **params
    ) -> Paginator[Place]:
        return self.client.paginate(
            get_places_nearby, Place, nelat=nelat, nelng=nelng, swlat=swlat, swlng=swlng, **params
        )
