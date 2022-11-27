from typing import Optional

from pyinaturalist.controllers import BaseController
from pyinaturalist.docs import document_controller_params
from pyinaturalist.models import Taxon
from pyinaturalist.paginator import IDPaginator, Paginator
from pyinaturalist.v1 import get_taxa, get_taxa_autocomplete, get_taxa_by_id

IDS_PER_REQUEST = 30


class TaxonController(BaseController):
    """:fa:`dove` Controller for Taxon requests"""

    def __call__(self, taxon_id: int, **kwargs) -> Optional[Taxon]:
        """Get a single taxon by ID"""
        return self.from_ids(taxon_id, **kwargs).one()

    def from_ids(self, *taxon_ids: int, **params) -> Paginator[Taxon]:
        """Get taxa by ID

        Args:
            taxon_ids: One or more taxon IDs
        """
        return self.client.paginate(
            get_taxa_by_id,
            Taxon,
            cls=IDPaginator,
            ids=taxon_ids,
            ids_per_request=IDS_PER_REQUEST,
            **params
        )

    @document_controller_params(get_taxa_autocomplete)
    def autocomplete(self, **params) -> Paginator[Taxon]:
        return self.client.paginate(get_taxa_autocomplete, Taxon, **params)

    @document_controller_params(get_taxa)
    def search(self, **params) -> Paginator[Taxon]:
        return self.client.paginate(get_taxa, Taxon, **params)
