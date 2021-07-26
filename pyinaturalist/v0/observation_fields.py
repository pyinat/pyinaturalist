from typing import Any

from pyinaturalist.api_requests import get, put
from pyinaturalist.constants import API_V0_BASE_URL, JsonResponse
from pyinaturalist.converters import convert_all_timestamps
from pyinaturalist.docs import document_request_params
from pyinaturalist.docs import templates as docs
from pyinaturalist.pagination import add_paginate_all


@document_request_params(docs._search_query, docs._pagination)
@add_paginate_all(method='page')
def get_observation_fields(**params) -> JsonResponse:
    """Search observation fields. Observation fields are basically typed data fields that
    users can attach to observation.

    **API reference:** https://www.inaturalist.org/pages/api+reference#get-observation_fields

    Example:

        >>> get_observation_fields(q='number of individuals')
        >>> # Show just observation field IDs and names
        >>> from pprint import pprint
        >>> pprint({r['id']: r['name'] for r in response})

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_observation_fields.py

    Returns:
        Observation fields as a list of dicts
    """
    response = get(f'{API_V0_BASE_URL}/observation_fields.json', **params)
    obs_fields = response.json()
    obs_fields = convert_all_timestamps(obs_fields)
    return {'results': obs_fields}


def put_observation_field_values(
    observation_id: int,
    observation_field_id: int,
    value: Any,
    access_token: str,
    **kwargs,
) -> JsonResponse:
    # TODO: Also implement a put_or_update_observation_field_values() that deletes then recreates the field_value?
    # TODO: Return some meaningful exception if it fails because the field is already set.
    # TODO: It appears pushing the same value/pair twice in a row (but deleting it meanwhile via the UI)...
    # TODO: ...triggers an error 404 the second time (report to iNaturalist?)
    """Set an observation field (value) on an observation.
    Will fail if this observation field is already set for this observation.

    To find an `observation_field_id`, either user :py:func:`.get_observation_fields` or search
    on iNaturalist: https://www.inaturalist.org/observation_fields

    **API reference:** https://www.inaturalist.org/pages/api+reference#put-observation_field_values-id

    Example:
        >>> # First find an observation field by name, if the ID is unknown
        >>> response = get_observation_fields('vespawatch_id')
        >>> observation_field_id = response[0]['id']
        >>>
        >>> put_observation_field_values(
        >>>     observation_id=7345179,
        >>>     observation_field_id=observation_field_id,
        >>>     value=250,
        >>>     access_token=token,
        >>> )

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/put_observation_field_value_result.json
                :language: javascript

    Args:
        observation_id: ID of the observation receiving this observation field value
        observation_field_id: ID of the observation field for this observation field value
        value: Value for the observation field
        access_token: The access token, as returned by :func:`get_access_token()`

    Returns:
        The newly updated field value record
    """
    json_body = {
        'observation_field_value': {
            'observation_id': observation_id,
            'observation_field_id': observation_field_id,
            'value': value,
        }
    }

    response = put(
        f'{API_V0_BASE_URL}/observation_field_values/{observation_field_id}',
        access_token=access_token,
        json=json_body,
        **kwargs,
    )
    return response.json()
