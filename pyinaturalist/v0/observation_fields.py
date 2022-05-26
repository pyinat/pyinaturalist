from typing import Any

from pyinaturalist.constants import API_V0, JsonResponse
from pyinaturalist.converters import convert_all_timestamps
from pyinaturalist.docs import document_request_params
from pyinaturalist.docs import templates as docs
from pyinaturalist.session import get, put


@document_request_params(docs._search_query, docs._pagination)
def get_observation_fields(**params) -> JsonResponse:
    """Search observation fields. Observation fields are basically typed data fields that
    users can attach to observation.

    .. rubric:: Notes

    * API reference: :v0:`GET /observation_fields <get-observation_fields>`
    * This endpoint does not support the ``per_page`` parameter

    Example:

        >>> get_observation_fields(q='number of individuals')
        >>> # Show just observation field IDs and names
        >>> from pprint import pprint
        >>> pprint({r['id']: r['name'] for r in response})

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_observation_fields.py

    Returns:
        Observation fields
    """
    all_pages = params.pop('page', None)
    params['page'] = 1
    params['per_page'] = 30  # This seems to return 30 results regardless of the per_page param
    obs_fields = get(f'{API_V0}/observation_fields.json', **params).json()

    # This endpoint returns a list with no pagination metadata, so iterate until there are no more pages
    if all_pages:
        page_results = obs_fields
        while len(page_results) == 30:
            params['page'] += 1
            page_results = get(f'{API_V0}/observation_fields.json', **params).json()
            obs_fields.extend(page_results)

    obs_fields = convert_all_timestamps(obs_fields)
    return {'results': obs_fields, 'total_results': len(obs_fields)}


@document_request_params(docs._ofvs, docs._access_token)
def put_observation_field_values(
    observation_id: int, observation_field_id: int, value: Any, **params
) -> JsonResponse:
    """Set an observation field value on an observation

    .. rubric:: Notes

    * :fa:`lock` :ref:`Requires authentication <auth>`
    * API reference: :v0:`PUT /observation_field_values/{id} <put-observation_field_values-id>`
    * The request will fail if this observation field is already set for this observation
    * To find an ``observation_field_id``, either user :py:func:`.get_observation_fields` or
      `search observation fields on iNaturalist <https://www.inaturalist.org/observation_fields>`_

    Example:
        >>> # First find an observation field by name, if the ID is unknown
        >>> response = get_observation_fields('vespawatch_id')
        >>> observation_field_id = response[0]['id']

        >>> put_observation_field_values(
        ...     observation_id=7345179,
        ...     observation_field_id=observation_field_id,
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
        'observation_field_value': {
            'observation_id': observation_id,
            'observation_field_id': observation_field_id,
            'value': value,
        }
    }
    response = put(f'{API_V0}/observation_field_values/{observation_field_id}', json=body, **params)
    return response.json()
