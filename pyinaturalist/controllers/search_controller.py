from pyinaturalist.constants import MultiInt, MultiStr
from pyinaturalist.controllers import BaseController
from pyinaturalist.models import SearchResult
from pyinaturalist.v1 import search


class SearchController(BaseController):
    """:fa:`search` Unified text search"""

    def __call__(
        self,
        q: str,
        sources: MultiStr | None = None,
        place_id: MultiInt | None = None,
        locale: str | None = None,
        preferred_place_id: int | None = None,
        **params,
    ) -> list[SearchResult]:
        """A unified text search endpoint for places, projects, taxa, and/or users

        .. rubric:: Notes

        * API reference: :v1:`GET /search <Search/get_search>`

        Example:
            >>> response = client.search(q='odonat')
            >>> pprint(response)
            ID        Type      Score   Name
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            47792     Taxon     9.45    Order Odonata (Dragonflies And Damselflies)
            113562    Place     7.70    Odonates of Peninsular India and Sri Lanka
            9978      Project   7.27    Ohio Dragonfly Survey (Ohio Odonata Survey)
            5665218   User      6.10    odonatachr

        Args:
            q: Search query
            sources: Object types to search
            place_id: Results must be associated with this place
            locale: Locale preference for taxon common names
            preferred_place_id: Place preference for regional taxon common names

        Returns:
            Response dict containing search results
        """
        response = search(
            q,
            sources=sources,
            place_id=place_id,
            locale=locale,
            preferred_place_id=preferred_place_id,
            **params,
        )
        return SearchResult.from_json_list(response)
