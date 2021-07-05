from logging import getLogger

from pyinaturalist.constants import JsonResponse
from pyinaturalist.converters import convert_all_timestamps, convert_generic_timestamps
from pyinaturalist.docs import document_request_params
from pyinaturalist.docs import templates as docs
from pyinaturalist.v1 import get_v1

logger = getLogger(__name__)


def get_user_by_id(user_id: int, **params) -> JsonResponse:
    """Get a user by ID.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Users/get_users_id

    Args:
        user_id: Get the user with this ID. Only a single ID is allowed per request.

    Example:

        >>> response = get_user_by_id(123456)
        >>> pprint(response)
        [1234] my_username

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_user_by_id.py

    Returns:
        Response dict containing user record
    """
    response = get_v1('users', ids=[user_id], **params)
    results = response.json()['results']
    if not results:
        return {}
    return convert_generic_timestamps(results[0])


@document_request_params([docs._search_query, docs._project_id, docs._pagination])
def get_users_autocomplete(q: str, **params) -> JsonResponse:
    """Given a query string, return users with names or logins starting with the search term

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Users/get_users_autocomplete

    Note: Pagination is supported; default page size is 6, and max is 100.

    Example:

        >>> response = get_taxa_autocomplete(q='my_userna')
        >>> pprint(response)
        [1234] my_username
        [12345] my_username_2

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_users_autocomplete.py

    Returns:
        Response dict containing user records
    """
    response = get_v1('users/autocomplete', q=q, **params)
    users = response.json()
    users['results'] = convert_all_timestamps(users['results'])
    return users
