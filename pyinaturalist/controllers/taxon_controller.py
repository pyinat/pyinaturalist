from attr import fields_dict

from pyinaturalist.constants import MAX_IDS_PER_REQUEST, MultiInt
from pyinaturalist.controllers import BaseController
from pyinaturalist.converters import ensure_list
from pyinaturalist.docs import copy_doc_signature
from pyinaturalist.docs import templates as docs
from pyinaturalist.models import Taxon
from pyinaturalist.paginator import IDPaginator, Paginator, WrapperPaginator
from pyinaturalist.v1 import get_taxa, get_taxa_autocomplete, get_taxa_by_id


class TaxonController(BaseController):
    """:fa:`dove` Controller for Taxon requests"""

    def __call__(self, taxon_id: int, **kwargs) -> Taxon | None:
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
            ids_per_request=MAX_IDS_PER_REQUEST,
            **params,
        )

    @copy_doc_signature(docs._taxon_params)
    def autocomplete(
        self,
        q: str | None = None,
        full_records: bool = False,
        exact_match: bool = False,
        **params,
    ) -> Paginator[Taxon]:
        """Given a query string, return taxa with names starting with the search term

        .. rubric:: Notes

        * API reference: :v1:`GET /taxa/autocomplete <Taxa/get_taxa_autocomplete>`
        * There appears to currently be a bug in the API that causes ``per_page`` to not have any effect.
        * ``exact_match`` is a best effort to get an exact match on common name. Due to lack of
          standardization and uniqueness in common names, though, multiple results are still likely.
          Results are sorted by observation count, so the first result is more likely to be what you're
          looking for. Filtering by rank will further increase your chances.

        Examples:

            Get all matches:

            >>> taxa = client.taxa.autocomplete(q='vespi').all()

            Search for only exact matches that are species, and get the first result:

            >>> best_guess = client.taxa.autocomplete(q='raven', exact_match=True, rank='species').one()
            >>> print(best_guess)
            "Taxon(id=8010, full_name=Corvus corax (Common Raven))"

            Verify the term that was matched (if different from preferred_common_name):

            >>> print(best_guess.matched_term)
            "Raven"

        Args:
            full_records: Fetch full taxon records by ID for each autocomplete match
            exact_match: Filter results to only taxa whose common name or matched term exactly
                matches ``q`` (case-insensitive).
        """
        query = self.client.paginate(get_taxa_autocomplete, Taxon, q=q, **params)
        if not (exact_match or full_records):
            return query

        taxa = query.all()
        if exact_match:
            taxa = self._filter_matches(taxa, q)
        if full_records:
            taxa = self._populate_all(taxa, **params)
        return WrapperPaginator(taxa)

    def _filter_matches(self, taxa: list[Taxon], q: str | None) -> list[Taxon]:
        q = (q or '').lower()
        filtered = [
            t
            for t in taxa
            if (t.preferred_common_name or '').lower() == q or (t.matched_term or '').lower() == q
        ]
        return sorted(filtered, key=lambda t: t.observations_count or 0, reverse=True)

    def _populate_all(self, taxa: list[Taxon], **params) -> list[Taxon]:
        """Populate all autocomplete matches with a full taxon record"""
        taxa_by_id = {t.id: t for t in taxa}
        full_taxa_by_id = {t.id: t for t in self.from_ids(list(taxa_by_id), **params).all()}
        # These haven't been returned to the user yet, so we can replace them rather than modify in-place
        results = [full_taxa_by_id[tid] for tid in taxa_by_id if tid in full_taxa_by_id]
        for taxon in results:
            taxon.matched_term = taxa_by_id[taxon.id].matched_term
        return results

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
