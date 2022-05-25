from pyinaturalist.constants import API_V1, JsonResponse
from pyinaturalist.converters import convert_all_coordinates, convert_all_timestamps
from pyinaturalist.docs import document_request_params
from pyinaturalist.docs import templates as docs
from pyinaturalist.session import get


@document_request_params(docs._search_params, docs._pagination)
def search(q: str, **params) -> JsonResponse:
    """A unified search endpoint for places, projects, taxa, and/or users

    .. rubric:: Notes

    * API reference: :v1:`GET /search <Search/get_search>`

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
    response = get(f'{API_V1}/search', q=q, **params)
    search_results = response.json()
    search_results['results'] = convert_all_timestamps(search_results['results'])
    search_results['results'] = convert_all_coordinates(search_results['results'])
    return search_results
