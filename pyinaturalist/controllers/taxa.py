from typing import List

from pyinaturalist.controllers import BaseController
from pyinaturalist.docs import document_controller_params
from pyinaturalist.models import Taxon
from pyinaturalist.v1 import get_taxa, get_taxa_autocomplete, get_taxa_by_id


class TaxonController(BaseController):
    """:fa:`dove,style=fas` Controller for taxon requests"""

    def from_id(self, *taxon_ids, **params) -> List[Taxon]:
        """Get taxa by ID

        Args:
            taxon_ids: One or more taxon IDs
        """
        response = get_taxa_by_id(taxon_ids, **params, **self.client.settings)
        return Taxon.from_json_list(response)  # type: ignore

    @document_controller_params(get_taxa_autocomplete)
    def autocomplete(self, **params) -> List[Taxon]:
        response = get_taxa_autocomplete(**params, **self.client.settings)
        return Taxon.from_json_list(response)  # type: ignore

    @document_controller_params(get_taxa)
    def search(self, **params) -> List[Taxon]:
        response = get_taxa(**params, **self.client.settings)
        return Taxon.from_json_list(response)  # type: ignore
