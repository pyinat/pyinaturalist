from typing import Any, Union

from pyinaturalist.constants import API_V1, JsonResponse
from pyinaturalist.docs import document_request_params
from pyinaturalist.docs import templates as docs
from pyinaturalist.session import delete, post


@document_request_params(docs._ofvs, docs._access_token)
def set_observation_field(
    observation_id: int, observation_field_id: int, value: Any, **params
) -> JsonResponse:
    """Create or update an observation field value on an observation

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * API reference: :v1:`POST /observation_field_values/{id} <post_observation_field_values>`
    * To find an ``observation_field_id``, either user :py:func:`.get_observation_fields` or
      `search observation fields on iNaturalist <https://www.inaturalist.org/observation_fields>`_

    Example:
        >>> # First find an observation field by name, if the ID is unknown:
        >>> response = get_observation_fields('vespawatch_id')
        >>> observation_field_id = response[0]['id']

        >>> set_observation_field(
        ...     7345179,
        ...     observation_field_id,
        ...     value=250,
        ...     access_token=token,
        ... )

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/post_put_observation_field_value.json
                :language: javascript

    Returns:
        The newly updated field value record
    """
    body = {
        'observation_id': observation_id,
        'observation_field_id': observation_field_id,
        'value': value,
    }
    response = post(f'{API_V1}/observation_field_values', json=body, **params)
    return response.json()


def delete_observation_field(observation_field_value_id: Union[int, str], **params) -> JsonResponse:
    """Delete an observation field value from an observation

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * API reference: :v1:`DELETE /observation_field_values/{id} <delete_observation_field_values_id>`

    Example:
        >>> # Observation field value IDs can be found on observation records:
        >>> response = get_observation(70963477)
        >>> ofv_ids = [ofv['id'] for ofv in response['ofvs']]

        >>> for ofv_id in ofv_ids:
        ...     delete_observation_field(ofv_id)


    Args:
        observation_field_value_id: ID or UUID of the observation field value to delete
        access_token: An access token required for user authentication, as returned by :py:func:`.get_access_token()`
    """
    response = delete(f'{API_V1}/observation_field_values/{observation_field_value_id}', **params)
    return response.json()
