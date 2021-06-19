from pyinaturalist.api_docs import document_request_params
from pyinaturalist.api_docs import templates as docs
from pyinaturalist.constants import JsonResponse
from pyinaturalist.converters import convert_all_coordinates, convert_all_timestamps
from pyinaturalist.v1 import get_v1


@document_request_params([docs._search_params, docs._pagination])
def search(q: str, **params) -> JsonResponse:
    """A unified search endpoint for places, projects, taxa, and/or users

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Search/get_search

    Example:

        >>> response = search(q='odonat')
        >>> pprint(response)
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
    response = get_v1('search', params={'q': q, **params})
    search_results = response.json()
    search_results['results'] = convert_all_timestamps(search_results['results'])
    search_results['results'] = convert_all_coordinates(search_results['results'])
    return search_results
