from typing import Any

from pyinaturalist.constants import IntOrStr, JsonResponse
from pyinaturalist.controllers import BaseController
from pyinaturalist.models import ObservationField
from pyinaturalist.v0 import get_observation_fields
from pyinaturalist.v1 import delete_observation_field, set_observation_field


class ObservationFieldController(BaseController):
    """:fa:`tag` Controller for ObservationField and ObservationFieldValue requests"""

    def search(self, q: str | None = None, **params) -> list[ObservationField]:
        """Search observation fields by name.

        .. rubric:: Notes

        * API reference: :v0:`GET /observation_fields <get-observation_fields>`
        * This uses the v0 API endpoint, which does not support ``per_page``

        Example:
            >>> fields = client.observation_fields.search('vespawatch_id')
            >>> pprint(fields)
             ID     Type   Name             Description
             ...

        Args:
            q: Search query for observation field name
        """
        response = self.client.request(get_observation_fields, q=q, **params)
        return ObservationField.from_json_list(response['results'])

    def set(
        self,
        observation_id: int,
        observation_field_id: int,
        value: Any,
        **params,
    ) -> JsonResponse:
        """Create or update an observation field value on an observation.

        .. rubric:: Notes

        * :fa:`lock` :ref:`Requires authentication <auth>`
        * API reference: :v1:`POST /observation_field_values <post_observation_field_values>`
        * To find an ``observation_field_id``, use :py:meth:`search` or
          `search on iNaturalist <https://www.inaturalist.org/observation_fields>`_

        Example:
            First find an observation field by name, if the ID is unknown:

            >>> fields = client.observation_fields.search('vespawatch_id')
            >>> field_id = fields[0].id

            Then set the value on an observation:

            >>> client.observation_fields.set(
            ...     observation_id=7345179,
            ...     observation_field_id=field_id,
            ...     value=250,
            ... )

        Args:
            observation_id: ID of the observation receiving this observation field value
            observation_field_id: ID of the observation field for this observation field value
            value: Value for the observation field

        Returns:
            The newly created or updated observation field value record
        """
        return self.client.request(
            set_observation_field,
            auth=True,
            observation_id=observation_id,
            observation_field_id=observation_field_id,
            value=value,
            **params,
        )

    def delete(self, observation_field_value_id: IntOrStr, **params):
        """Delete an observation field value from an observation.

        .. rubric:: Notes

        * :fa:`lock` :ref:`Requires authentication <auth>`
        * API reference: :v1:`DELETE /observation_field_values/{id} <delete_observation_field_values_id>`

        Example:
            Observation field value IDs can be found on observation records:

            >>> obs = client.observations(70963477)
            >>> for ofv in obs.ofvs:
            ...     client.observation_fields.delete(ofv.id)

        Args:
            observation_field_value_id: ID or UUID of the observation field value to delete
        """
        self.client.request(
            delete_observation_field,
            auth=True,
            observation_field_value_id=observation_field_value_id,
            **params,
        )
