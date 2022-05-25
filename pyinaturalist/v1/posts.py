from pyinaturalist.constants import API_V1, ListResponse
from pyinaturalist.converters import convert_all_coordinates, convert_all_timestamps
from pyinaturalist.docs import document_request_params
from pyinaturalist.docs import templates as docs
from pyinaturalist.session import get


@document_request_params(docs._get_posts)
def get_posts(**params) -> ListResponse:
    """Search posts

    .. rubric:: Notes

    * API reference: :v1:`GET /posts <Posts/get_posts>`

    Example:
        Get journal posts from user 'username'

        >>> response = get_posts(login='username')

    Returns:
        List containing journal posts from the iNaturalist site
    """
    response = get(f'{API_V1}/posts', **params)

    posts = response.json()
    posts = convert_all_coordinates(posts)
    posts = convert_all_timestamps(posts)

    return posts
