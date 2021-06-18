from pyinaturalist.api_docs import document_request_params
from pyinaturalist.api_docs import templates as docs
from pyinaturalist.constants import JsonResponse, MultiInt
from pyinaturalist.converters import convert_all_timestamps
from pyinaturalist.pagination import add_paginate_all
from pyinaturalist.request_params import convert_rank_range
from pyinaturalist.v1 import get_v1


@document_request_params([docs._taxon_params, docs._taxon_id_params, docs._pagination])
@add_paginate_all(method='page')
def get_taxa(**params) -> JsonResponse:
    """Given zero to many of following parameters, get taxa matching the search criteria.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa

    Example:

        >>> response = get_taxa(q='vespi', rank=['genus', 'family'])
        >>> print(format_taxa(response))
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
    response = get_v1('taxa', params=params)
    taxa = response.json()
    taxa['results'] = convert_all_timestamps(taxa['results'])
    return taxa


def get_taxa_by_id(taxon_id: MultiInt, user_agent: str = None) -> JsonResponse:
    """Get one or more taxa by ID.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa_id

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
        taxon_id: Get taxa with this ID. Multiple values are allowed.

    Returns:
        Response dict containing taxon records
    """
    response = get_v1('taxa', ids=taxon_id, user_agent=user_agent)
    taxa = response.json()
    taxa['results'] = convert_all_timestamps(taxa['results'])
    return taxa


@document_request_params([docs._taxon_params])
def get_taxa_autocomplete(**params) -> JsonResponse:
    """Given a query string, return taxa with names starting with the search term

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa_autocomplete

    **Note:** There appears to currently be a bug in the API that causes ``per_page`` to not have
    any effect.

    Example:

        Get just the name of the first matching taxon:

        >>> response = get_taxa_autocomplete(q='vespi')
        >>> print(response['results'][0]['name'])
        'Vespidae'

        Get basic info for taxa in response:

        >>> print(format_taxa(response, align=True))
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
    response = get_v1('taxa/autocomplete', params=params)
    return response.json()
