from pyinaturalist import api_docs as docs
from pyinaturalist.constants import JsonResponse
from pyinaturalist.forge_utils import document_request_params
from pyinaturalist.response_format import convert_all_coordinates, convert_all_timestamps
from pyinaturalist.v1 import get_v1


@document_request_params([docs._search_params, docs._pagination])
def search(q: str, **params) -> JsonResponse:
    """A unified search endpoint for places, projects, taxa, and/or users

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Search/get_search

    Example:

        >>> response = search(q='odonat')
        >>> print(format_search_results(response, align=True))
        [Taxon  ] [47792   ] Order: Odonata (Dragonflies and Damselflies)
        [Place  ] [113562  ] Odonates of Peninsular India and Sri Lanka
        [Project] [9978    ] Ohio Dragonfly Survey  (Ohio Odonata Survey)
        [User   ] [113886  ] odonatanb (Gilles Belliveau)


        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_search.py

    Returns:
        Response dict containing search results
    """
    r = get_v1('search', params={'q': q, **params})
    r.raise_for_status()
    search_results = r.json()
    search_results['results'] = convert_all_timestamps(search_results['results'])
    search_results['results'] = convert_all_coordinates(search_results['results'])
    return search_results
