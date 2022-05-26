from logging import getLogger

from pyinaturalist.constants import API_V1, JsonResponse, MultiInt
from pyinaturalist.converters import convert_all_timestamps
from pyinaturalist.docs import document_request_params
from pyinaturalist.docs import templates as docs
from pyinaturalist.session import get

logger = getLogger(__name__)


@document_request_params(docs._message_id, docs._access_token)
def get_message_by_id(message_id: MultiInt, **params) -> JsonResponse:
    """Get a message by ID

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * API reference: :v1:`GET /messages/{id} <Messages/get_messages_id>`

    Example:
        >>> response = get_messages(123456)
        >>> pprint(response)

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_messages.json

    Returns:
        Response dict containing user record
    """
    response = get(f'{API_V1}/messages', ids=message_id, **params)
    messages = response.json()
    messages['results'] = convert_all_timestamps(messages['results'])
    return messages


@document_request_params(docs._message_params, docs._access_token)
def get_messages(**params) -> JsonResponse:
    """Get messages from the user's inbox

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * API reference: :v1:`GET /messages <Messages/get_messages>`

    Example:
        >>> response = get_messages()
        >>> pprint(response)

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_messages.json

    Returns:
        Response dict containing user record
    """
    # `threads` is not compatible with `q` param, and includes totals from both inbox and sent
    if params.get('threads') is True:
        params['box'] = 'any'
        params['q'] = None

    response = get(f'{API_V1}/messages', **params)
    messages = response.json()
    messages['results'] = convert_all_timestamps(messages['results'])
    return messages


def get_unread_meassage_count(**params) -> int:
    """Get the number of unread messages in the user's inbox

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * API reference: :v1:`GET /messages/unread <Messages/get_messages_unread>`

    Example:
        >>> get_unread_meassage_count()
        12

    Returns:
        Unread message count
    """
    response = get(f'{API_V1}/messages/unread', **params)
    try:
        return int(response.json()['count'])
    except (KeyError, TypeError, ValueError):
        logger.error(f'Failed to get unread message count: {response.text}', exc_info=True)
        return 0
