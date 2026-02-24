from copy import deepcopy

from pyinaturalist.constants import API_V2, JsonResponse, MultiInt, RequestParams
from pyinaturalist.converters import convert_all_timestamps, ensure_list
from pyinaturalist.docs import document_request_params
from pyinaturalist.docs import templates as docs
from pyinaturalist.paginator import paginate_all
from pyinaturalist.request_params import convert_rank_range
from pyinaturalist.session import get, post


@document_request_params(
    docs._taxon_params,
    docs._taxon_id_params,
    docs._observation_v2,
    docs._pagination,
)
def get_taxa(**params) -> JsonResponse:
    """Search taxa

    .. rubric:: Notes

    * API reference: :v2:`GET /taxa <Taxa/get_taxa>`
    * See `iNaturalist API v2 documentation <https://api.inaturalist.org/v2/docs>`_ for details on
      selecting return fields using ``fields`` parameter

    Example:
        >>> response = get_taxa(q='vespi', rank=['genus', 'family'], fields='all')
        >>> pprint(response)
        [52747] Family: Vespidae (Hornets, Paper Wasps, Potter Wasps, and Allies)
        [92786] Genus: Vespicula
        [646195] Genus: Vespiodes
        ...

        .. dropdown:: Example Response (default/minimal)
            :color: primary
            :icon: code-square

            .. literalinclude:: ../sample_data/v2/get_taxa_minimal.json
                :language: JSON

        .. dropdown:: Example Response (all fields)
            :color: primary
            :icon: code-square

            .. literalinclude:: ../sample_data/v2/get_taxa_full.json
                :language: JSON

    Returns:
        Response dict containing taxon records
    """
    params = convert_rank_range(params)
    except_fields = params.pop('except_fields', None)

    if params.get('fields') and except_fields:
        raise ValueError('Cannot use both fields and except_fields')

    # Request all fields except those specified
    if except_fields:
        params['fields'] = deepcopy(ALL_TAXA_FIELDS)
        for k in except_fields:
            params['fields'].pop(k, None)

    if params.get('fields') not in ['all', None]:
        taxa = _get_post_taxa(params)
    else:
        taxa = _get_taxa(params)

    taxa['results'] = convert_all_timestamps(taxa['results'])
    return taxa


def get_taxa_by_id(
    taxon_id: MultiInt,
    **params,
) -> JsonResponse:
    """Get one or more taxa by ID

    .. rubric:: Notes

    * API reference: :v2:`GET /taxa/{id} <Taxa/get_taxa_id>`

    Example:
        >>> response = get_taxa_by_id(343248)
        >>> print(response['results'][0]['name'])
        'Polistinae'

        .. dropdown:: Example Response (default/minimal)
            :color: primary
            :icon: code-square

            .. literalinclude:: ../sample_data/v2/get_taxa_by_id_minimal.json
                :language: JSON

        .. dropdown:: Example Response (all fields)
            :color: primary
            :icon: code-square

            .. literalinclude:: ../sample_data/v2/get_taxa_by_id_full.json
                :language: JSON

    Args:
        taxon_id: Get taxon with this ID. Multiple values are allowed.

    Returns:
        Response dict containing taxon records
    """
    except_fields = params.pop('except_fields', None)

    if params.get('fields') and except_fields:
        raise ValueError('Cannot use both fields and except_fields')

    if except_fields:
        params['fields'] = deepcopy(ALL_TAXA_FIELDS)
        for k in except_fields:
            params['fields'].pop(k, None)

    n_ids = len(ensure_list(taxon_id))
    if params.get('fields') not in ['all', None] or n_ids > 30:
        body = dict(params)
        body['id'] = taxon_id
        query_params = {k: body.pop(k) for k in ['page', 'per_page'] if k in body}
        headers = {'X-HTTP-Method-Override': 'GET'}
        taxa = post(f'{API_V2}/taxa', headers=headers, json=body, **query_params).json()
    else:
        taxa = get(f'{API_V2}/taxa', ids=taxon_id, **params).json()

    taxa['results'] = convert_all_timestamps(taxa['results'])
    return taxa


@document_request_params(docs._taxon_params, docs._observation_v2)
def get_taxa_autocomplete(**params) -> JsonResponse:
    """Given a query string, return taxa with names starting with the search term

    .. rubric:: Notes

    * API reference: :v2:`GET /taxa/autocomplete <Taxa/get_taxa_autocomplete>`

    Example:
        >>> response = get_taxa_autocomplete(q='vespi')
        >>> print(response['results'][0]['name'])
        'Vespidae'

    Returns:
        Response dict containing taxon records
    """
    params = convert_rank_range(params)
    except_fields = params.pop('except_fields', None)

    if params.get('fields') and except_fields:
        raise ValueError('Cannot use both fields and except_fields')

    if except_fields:
        params['fields'] = deepcopy(ALL_TAXA_FIELDS)
        for k in except_fields:
            params['fields'].pop(k, None)

    if params.get('fields') not in ['all', None]:
        headers = {'X-HTTP-Method-Override': 'GET'}
        body = params
        return post(f'{API_V2}/taxa/autocomplete', headers=headers, json=body).json()
    else:
        return get(f'{API_V2}/taxa/autocomplete', **params).json()


def get_taxa_iconic(**params) -> JsonResponse:
    """Get all iconic taxa

    .. rubric:: Notes

    * API reference: :v2:`GET /taxa/iconic <Taxa/get_taxa_iconic>`

    Example:
        >>> response = get_taxa_iconic(fields='all')

        .. dropdown:: Example Response (all fields)
            :color: primary
            :icon: code-square

            .. literalinclude:: ../sample_data/v2/get_taxa_iconic_full.json
                :language: JSON

    Returns:
        Response dict containing iconic taxon records
    """
    except_fields = params.pop('except_fields', None)

    if params.get('fields') and except_fields:
        raise ValueError('Cannot use both fields and except_fields')

    if except_fields:
        params['fields'] = deepcopy(ALL_TAXA_FIELDS)
        for k in except_fields:
            params['fields'].pop(k, None)

    if params.get('fields') not in ['all', None]:
        headers = {'X-HTTP-Method-Override': 'GET'}
        body = params
        return post(f'{API_V2}/taxa/iconic', headers=headers, json=body).json()
    else:
        return get(f'{API_V2}/taxa/iconic', **params).json()


def _get_taxa(params: RequestParams) -> JsonResponse:
    if params.get('page') == 'all':
        return paginate_all(get, f'{API_V2}/taxa', **params)
    else:
        return get(f'{API_V2}/taxa', **params).json()


def _get_post_taxa(params: RequestParams) -> JsonResponse:
    """Use POST method to get taxa with selection of return fields."""
    headers = {'X-HTTP-Method-Override': 'GET'}
    body = params
    query_params = {k: body.pop(k) for k in ['page', 'per_page'] if k in body}
    if query_params.get('page') == 'all':
        return paginate_all(
            post,
            f'{API_V2}/taxa',
            method='id',
            headers=headers,
            json=body,
            **query_params,
        )
    else:
        return post(f'{API_V2}/taxa', headers=headers, json=body, **query_params).json()


# The full `fields` value to request all taxa details
ALL_TAXA_FIELDS = {
    'ancestor_ids': True,
    'ancestry': True,
    'atlas_id': True,
    'complete_species_count': True,
    'current_synonymous_taxon_ids': True,
    'default_photo': {
        'id': True,
        'attribution': True,
        'attribution_name': True,
        'flags': True,
        'license_code': True,
        'medium_url': True,
        'original_dimensions': True,
        'square_url': True,
        'url': True,
    },
    'extinct': True,
    'flag_counts': {
        'resolved': True,
        'unresolved': True,
    },
    'iconic_taxon_id': True,
    'iconic_taxon_name': True,
    'is_active': True,
    'matched_term': True,
    'name': True,
    'observations_count': True,
    'parent_id': True,
    'preferred_common_name': True,
    'provisional': True,
    'rank': True,
    'rank_level': True,
    'taxon_changes_count': True,
    'taxon_schemes_count': True,
    'wikipedia_url': True,
}
