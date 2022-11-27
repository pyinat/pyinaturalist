from pyinaturalist.constants import API_V1, JsonResponse, MultiInt
from pyinaturalist.converters import convert_all_timestamps
from pyinaturalist.docs import document_request_params
from pyinaturalist.docs import templates as docs
from pyinaturalist.paginator import paginate_all
from pyinaturalist.request_params import convert_rank_range
from pyinaturalist.session import get


@document_request_params(docs._taxon_params, docs._taxon_id_params, docs._pagination)
def get_taxa(**params) -> JsonResponse:
    """Search taxa

    .. rubric:: Notes

    * API reference: :v1:`GET /taxa <Taxa/get_taxa>`

    Example:
        >>> response = get_taxa(q='vespi', rank=['genus', 'family'])
        >>> pprint(response)
        [52747] Family: Vespidae (Hornets, Paper Wasps, Potter Wasps, and Allies)
        [92786] Genus: Vespicula
        [646195] Genus: Vespiodes
        ...

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_taxa.json
                :language: JSON

    Returns:
        Response dict containing taxon records
    """
    params = convert_rank_range(params)
    if params.get('page') == 'all':
        taxa = paginate_all(get, f'{API_V1}/taxa', **params)
    else:
        taxa = get(f'{API_V1}/taxa', **params).json()

    taxa['results'] = convert_all_timestamps(taxa['results'])
    return taxa


def get_taxa_by_id(taxon_id: MultiInt, **params) -> JsonResponse:
    """Get one or more taxa by ID

    .. rubric:: Notes

    * API reference: :v1:`GET /taxa/{id} <Taxa/get_taxa_id>`

    Example:
        >>> response = get_taxa_by_id(343248)
        >>> basic_fields = ['preferred_common_name', 'observations_count', 'wikipedia_url', 'wikipedia_summary']
        >>> print({f: response['results'][0][f] for f in basic_fields})
        {
            'preferred_common_name': 'Paper Wasps',
            'observations_count': 69728,
            'wikipedia_url': 'http://en.wikipedia.org/wiki/Polistinae',
            'wikipedia_summary': 'The Polistinae are eusocial wasps closely related to yellow jackets...',
        }

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_taxa_by_id.py

    Args:
        taxon_id: Get taxon with this ID. Multiple values are allowed.

    Returns:
        Response dict containing taxon records
    """
    response = get(f'{API_V1}/taxa', ids=taxon_id, **params)
    taxa = response.json()
    taxa['results'] = convert_all_timestamps(taxa['results'])
    return taxa


@document_request_params(docs._taxon_params)
def get_taxa_autocomplete(**params) -> JsonResponse:
    """Given a query string, return taxa with names starting with the search term

    .. rubric:: Notes

    * API reference: :v1:`GET /taxa/autocomplete <Taxa/get_taxa_autocomplete>`
    * There appears to currently be a bug in the API that causes ``per_page`` to not have any effect.

    Example:
        Get just the name of the first matching taxon:

        >>> response = get_taxa_autocomplete(q='vespi')
        >>> print(response['results'][0]['name'])
        'Vespidae'

        Get basic info for taxa in response:

        >>> pprint(response)
        [52747   ]       Family: Vespidae (Hornets, Paper Wasps, Potter Wasps, and Allies)
        [84738   ]    Subfamily: Vespinae (Hornets and Yellowjackets)
        [131878  ]      Species: Nicrophorus vespillo (Vespillo Burying Beetle)

        If you get unexpected matches, the search likely matched a synonym, either in the form of a
        common name or an alternative classification. Check the ``matched_term`` property for more
        info. For example:

        >>> first_result = get_taxa_autocomplete(q='zygoca')['results'][0]
        >>> first_result["name"]
        "Schlumbergera truncata"  # This doesn't look like our search term!
        >>> first_result["matched_term"]
        "Zygocactus truncatus"    # ...Because it matched an older synonym for Schlumbergera

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_taxa_autocomplete.py

        .. admonition:: Example Response (formatted)
            :class: toggle

            .. literalinclude:: ../sample_data/get_taxa_autocomplete_minified.py

    Returns:
        Response dict containing taxon records
    """
    params = convert_rank_range(params)
    response = get(f'{API_V1}/taxa/autocomplete', **params)
    return response.json()


def get_taxa_map_layers(taxon_id: int, **params) -> JsonResponse:
    """Get some additional taxon metadata, including:
    * GBIF taxon ID and URL
    * Whether the taxon has range data and/or listed places

    Example:
        >>> response = get_taxa_map_layers(343248)

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_taxa_map_layers.json
                :language: JSON

    Args:
        taxon_id: iNaturalist taxon ID. Only one value is allowed.
    """
    response = get(f'{API_V1}/taxa/{taxon_id}/map_layers', **params).json()
    response['gbif_url'] = f'https://www.gbif.org/species/{response["gbif_id"]}'
    return response
