from pyinaturalist.constants import API_V1, JsonResponse, MultiInt
from pyinaturalist.converters import convert_all_timestamps
from pyinaturalist.docs import document_request_params
from pyinaturalist.docs import templates as docs
from pyinaturalist.paginator import paginate_all
from pyinaturalist.request_params import convert_rank_range
from pyinaturalist.session import get


def get_identifications_by_id(identification_id: MultiInt, **params) -> JsonResponse:
    """Get one or more identification records by ID

    .. rubric:: Notes

    * API reference: :v1:`GET /identifications/{id} <Identifications/get_identifications_id>`

    Example:
        >>> get_identifications_by_id(155554373)

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_identifications.py

    Args:
        identification_id: Get taxa with this ID. Multiple values are allowed.

    Returns:
        Response dict containing identification records
    """
    response = get(f'{API_V1}/identifications', ids=identification_id, **params)
    identifications = response.json()
    identifications['results'] = convert_all_timestamps(identifications['results'])
    return identifications


@document_request_params(docs._identification_params, docs._pagination, docs._only_id)
def get_identifications(**params) -> JsonResponse:
    """Search identifications

    .. rubric:: Notes

    * API reference: :v1:`GET /identifications <Identifications/get_identifications>`

    Example:
        Get all of your own species-level identifications:

        >>> response = get_identifications(user_login='my_username', rank='species')
        >>> print([f"{i['user']['login']}: {i['taxon_id']} ({i['category']})" for i in response['results']])
        [155043569] Species: 76465 (leading) added on 2021-02-15 10:46:27-06:00 by jkcook
        [153668189] Species: 76465 (supporting) added on 2021-02-06 17:43:37+00:00 by jkcook
        [147500725] Species: 1163860 (improving) added on 2020-12-24 23:52:30+00:00 by jkcook
        ...

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_identifications.py

    Returns:
        Response dict containing identification records
    """
    params = convert_rank_range(params)
    if params.get('page') == 'all':
        identifications = paginate_all(get, f'{API_V1}/identifications', **params)
    else:
        identifications = get(f'{API_V1}/identifications', **params).json()

    identifications['results'] = convert_all_timestamps(identifications['results'])
    return identifications
