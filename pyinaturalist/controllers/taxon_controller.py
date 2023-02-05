from typing import Optional

from attr import fields_dict

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

    def populate(self, taxon: Taxon, **params) -> Taxon:
        """Update a partial Taxon record with full taxonomy info, including ancestors + children

        Args:
            taxon: A partial Taxon record

        Returns:
            The same Taxon record, updated with full taxonomy info
        """
        # Don't overwrite these keys if set by a previous API call
        preserve_keys = {'listed_taxa', 'matched_term', 'names'}

        full_taxon = self.from_ids(taxon.id, **params).one()
        for key in set(fields_dict(Taxon).keys()) - preserve_keys:
            # Use getters/setters for LazyProperty instead of temp attrs (cls.foo vs cls._foo)
            if hasattr(key, key.lstrip('_')):
                key = key.lstrip('_')
            setattr(taxon, key, getattr(full_taxon, key))
        return taxon
