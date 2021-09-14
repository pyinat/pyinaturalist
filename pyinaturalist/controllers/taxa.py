from pyinaturalist.controllers import BaseController
from pyinaturalist.docs import document_controller_params
from pyinaturalist.models import Taxon
from pyinaturalist.paginator import Paginator
from pyinaturalist.v1 import get_taxa, get_taxa_autocomplete, get_taxa_by_id


class TaxonController(BaseController):
    """:fa:`dove,style=fas` Controller for Taxon requests"""

    def from_id(self, *taxon_ids, **params) -> Paginator[Taxon]:
        """Get taxa by ID

        Args:
            taxon_ids: One or more taxon IDs
        """
        return self.client.paginate(get_taxa_by_id, Taxon, taxon_id=taxon_ids, **params)

    @document_controller_params(get_taxa_autocomplete)
    def autocomplete(self, **params) -> Paginator[Taxon]:
        return self.client.paginate(get_taxa_autocomplete, Taxon, **params)

    @document_controller_params(get_taxa)
    def search(self, **params) -> Paginator[Taxon]:
        return self.client.paginate(get_taxa, Taxon, **params)
