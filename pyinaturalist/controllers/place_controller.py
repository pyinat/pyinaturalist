from typing import Optional

from pyinaturalist.constants import IntOrStr, MultiIntOrStr
from pyinaturalist.controllers import BaseController
from pyinaturalist.converters import ensure_list
from pyinaturalist.models import Place
from pyinaturalist.paginator import AutocompletePaginator, Paginator
from pyinaturalist.v1 import get_places_autocomplete, get_places_by_id, get_places_nearby


class PlaceController(BaseController):
    """:fa:`location-dot` Controller for Place requests"""

    def __call__(self, place_id: IntOrStr, **kwargs) -> Optional[Place]:
        """Get a single place by ID

        Example:
            >>> client.places(67591)

        Args:
            place_ids: A single place ID
        """
        return self.from_ids(place_id, **kwargs).one()

    def from_ids(self, place_ids: MultiIntOrStr, **params) -> Paginator[Place]:
        """Get places by ID

        .. rubric:: Notes

        * API reference: :v1:`GET /places/{id} <Places/get_places_id>`

        Example:
            >>> client.places.from_ids([67591, 89191])

        Args:
            place_ids: One or more place IDs
        """
        return self.client.paginate(
            get_places_by_id, Place, place_id=ensure_list(place_ids), **params
        )

    def autocomplete(self, q: Optional[str] = None, **params) -> Paginator[Place]:
        """Given a query string, get places with names starting with the search term

        .. rubric:: Notes

        * API reference: :v1:`GET /places/autocomplete <Places/get_places_autocomplete>`

        Example:
            >>> client.places.autocomplete('Irkutsk')

        Args:
            q: Search query
        """
        return self.client.paginate(
            get_places_autocomplete,
            Place,
            cls=AutocompletePaginator,
            q=q,
            per_page=20,
            **params,
        )

    def nearby(
        self,
        nelat: float,
        nelng: float,
        swlat: float,
        swlng: float,
        name: Optional[str] = None,
        **params
    ) -> Paginator[Place]:
        """Search for places near a given location

        .. rubric:: Notes

        * API reference: :v1:`GET /places/nearby <get_places_nearby>`

        Example:
            >>> bounding_box = (150.0, -50.0, -149.999, -49.999)
            >>> client.places.nearby(*bounding_box)

        Args:
            nelat: NE latitude of bounding box
            nelng: NE longitude of bounding box
            swlat: SW latitude of bounding box
            swlng: SW longitude of bounding box
            name: Name must match this value
        """
        return self.client.paginate(
            get_places_nearby,
            Place,
            nelat=nelat,
            nelng=nelng,
            swlat=swlat,
            swlng=swlng,
            name=name,
            **params,
        )
