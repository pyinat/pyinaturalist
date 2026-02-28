from pyinaturalist.constants import (
    API_V1,
    MultiInt,
)
from pyinaturalist.controllers import BaseController
from pyinaturalist.converters import ensure_list
from pyinaturalist.docs import templates as docs
from pyinaturalist.docs.signatures import copy_doc_signature
from pyinaturalist.models import (
    Identification,
)
from pyinaturalist.paginator import IDPaginator, Paginator
from pyinaturalist.request_params import convert_rank_range

IDS_PER_REQUEST = 30


class IdentificationController(BaseController):
    """:fa:`binoculars` Controller for Identification requests"""

    def __call__(self, identification_id: int, **params) -> Identification | None:
        """Get a single identification by ID

        Example:
            >>> client.identifications(16227955)

        Args:
            identification_id: A single identification ID
        """
        return self.from_ids(identification_id, **params).one()

    def from_ids(self, identification_ids: MultiInt, **params) -> Paginator[Identification]:
        """Get one or more identifications by ID

        .. rubric:: Notes

        * :fas:`file-circle-plus` :ref:`Paginated endpoint <pagination>`
        * API reference: :v1:`GET /identifications/{id} <identifications/get_identifications_id>`

        Examples:
            >>> ids = client.identifications.from_ids(700305837).all()
            >>> ids = client.identifications.from_ids([700305837, 700306322]).all()

        Args:
            identification_ids: One or more identification IDs
        """

        def get_identifications_by_id(_identification_ids: MultiInt, **params):
            return self.client.session.request(
                'GET', f'{API_V1}/identifications', ids=_identification_ids, **params
            ).json()

        params = self.client.add_defaults(get_identifications_by_id, params)

        return IDPaginator(
            get_identifications_by_id,
            Identification,
            ids=ensure_list(identification_ids),
            ids_per_request=IDS_PER_REQUEST,
            **params,
        )

    @copy_doc_signature(docs._identification_params, docs._pagination, docs._only_id)
    def search(self, **params) -> Paginator[Identification]:
        """Search identifications

        .. rubric:: Notes

        * :fas:`file-circle-plus` :ref:`Paginated endpoint <pagination>`
        * API reference: :v1:`GET /identifications <Identifications/get_identifications>`

        Example:
            Get all of your own species-level identifications:

            >>> ids = client.identifications.search(user_login='my_username', rank='species').all()
        """

        def get_identifications(**params):
            return self.client.session.get(f'{API_V1}/identifications', **params).json()

        params = convert_rank_range(params)
        return self.client.paginate(get_identifications, Identification, **params)
