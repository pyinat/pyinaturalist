from pyinaturalist.constants import ListResponse
from pyinaturalist.converters import convert_all_coordinates, convert_all_timestamps
from pyinaturalist.docs import document_request_params
from pyinaturalist.docs import templates as docs
from pyinaturalist.v1 import get_v1


@document_request_params(docs._get_posts)
def get_posts(**params) -> ListResponse:
    """Search posts.

    **API reference:** https://api.inaturalist.org/v1/docs/#!/Posts/get_posts

    Example:

        Get journal posts from user 'username'

        >>> response = get_posts(
        >>>     login=myusername
        >>> )

    Returns:
        List containing journal posts from the iNaturalist site
    """
    response = get_v1('posts', **params)

    posts = response.json()
    posts = convert_all_coordinates(posts)
    posts = convert_all_timestamps(posts)

    return posts
