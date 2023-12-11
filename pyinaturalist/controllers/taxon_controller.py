from typing import Optional

from attr import fields_dict

from pyinaturalist.constants import MultiInt
from pyinaturalist.controllers import BaseController
from pyinaturalist.converters import ensure_list
from pyinaturalist.docs import copy_doc_signature
from pyinaturalist.docs import templates as docs
from pyinaturalist.models import Taxon
from pyinaturalist.paginator import IDPaginator, Paginator
from pyinaturalist.v1 import get_taxa, get_taxa_autocomplete, get_taxa_by_id

IDS_PER_REQUEST = 30


class TaxonController(BaseController):
    """:fa:`dove` Controller for Taxon requests"""

    def __call__(self, taxon_id: int, **kwargs) -> Optional[Taxon]:
        """Get a single taxon by ID

        Example:
            >>> client.taxa(343248)

        Args:
            taxon_id: A single taxon ID
            locale: Locale preference for taxon common names
            preferred_place_id: Place preference for regional taxon common names
            all_names: Include all taxon names in the response
        """
        return self.from_ids(taxon_id, **kwargs).one()

    def from_ids(self, taxon_ids: MultiInt, **params) -> Paginator[Taxon]:
        """Get one or more taxa by ID

        .. rubric:: Notes

        * API reference: :v1:`GET /taxa/{id} <Taxa/get_taxa_id>`


        Example:
            >>> client.get_taxa_by_id([3, 343248])

        Args:
            taxon_ids: One or more taxon IDs
            locale: Locale preference for taxon common names
            preferred_place_id: Place preference for regional taxon common names
            all_names: Include all taxon names in the response
        """

        params = self.client.add_defaults(get_taxa_by_id, params)
        return IDPaginator(
            get_taxa_by_id,
            Taxon,
            ids=ensure_list(taxon_ids),
            ids_per_request=IDS_PER_REQUEST,
            **params,
        )

    @copy_doc_signature(docs._taxon_params)
    def autocomplete(self, **params) -> Paginator[Taxon]:
        """Given a query string, return taxa with names starting with the search term

        .. rubric:: Notes

        * API reference: :v1:`GET /taxa/autocomplete <Taxa/get_taxa_autocomplete>`
        * There appears to currently be a bug in the API that causes ``per_page`` to not have any effect.

        Example:
            >>> client.taxa.autocomplete(q='vespi')
        """
        return self.client.paginate(get_taxa_autocomplete, Taxon, **params)

    @copy_doc_signature(docs._taxon_params, docs._taxon_id_params)
    def search(self, **params) -> Paginator[Taxon]:
        """Search taxa

        .. rubric:: Notes

        * API reference: :v1:`GET /taxa <Taxa/get_taxa>`

        Example:
            >>> client.taxa.search(q='vespi', rank=['genus', 'family'])
        """
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
            if hasattr(taxon, key.lstrip('_')):
                key = key.lstrip('_')
            setattr(taxon, key, getattr(full_taxon, key))
        return taxon
