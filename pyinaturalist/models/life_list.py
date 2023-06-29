"""Models for user life lists"""
from itertools import groupby
from typing import Any, Callable, Dict, Iterable, List, Optional

from rich.tree import Tree

from pyinaturalist.constants import JsonResponse
from pyinaturalist.models import (
    BaseModelCollection,
    Taxon,
    TaxonCount,
    define_model_collection,
    field,
)


@define_model_collection
class LifeList(BaseModelCollection):
    """:fa:`dove` :fa:`list` A user's life list, based on the schema of ``GET /observations/taxonomy``"""

    data: List[TaxonCount] = field(factory=list, converter=TaxonCount.from_json_list)
    count_without_taxon: int = field(default=0, doc='Number of observations without a taxon')
    user_id: int = field(default=None)

    @classmethod
    def from_json(cls, value: JsonResponse, user_id: Optional[int] = None, **kwargs) -> 'LifeList':
        count_without_taxon = value.get('count_without_taxon', 0)
        if 'results' in value:
            value = value['results']

        life_list_json = {
            'data': value,
            'user_id': user_id,
            'count_without_taxon': count_without_taxon,
        }
        return super(LifeList, cls).from_json(life_list_json)

    def get_count(self, taxon_id: int, count_field='descendant_obs_count') -> int:
        """Get an observation count for the specified taxon and its descendants, and handle unlisted taxa.
        **Note:** ``-1`` can be used an alias for ``count_without_taxon``.
        """
        if taxon_id == -1:
            return self.count_without_taxon
        return super().get_count(taxon_id, count_field=count_field)

    def tree(self) -> Taxon:
        """**Experimental**

        Organize this life list into a taxonomic tree

        Returns:
            Root taxon of the tree
        """
        return make_tree(self.data)


def make_tree(taxa: Iterable[Taxon], sort_key: Optional[Callable[[Taxon], Any]] = None) -> Taxon:
    """Organize a list of taxa into a taxonomic tree. Exepects exactly one root taxon.

    Returns:
        Root taxon of the tree
    """

    def default_sort(taxon):
        """Default sort key for taxon children"""
        return taxon.rank_level, taxon.name

    def sort_groupby(values, key):
        """Apply sorting then grouping using the same key"""
        return {k: list(group) for k, group in groupby(sorted(values, key=key), key=key)}

    def add_descendants(taxon) -> Taxon:
        """Recursively add taxon descendants"""
        taxon.children = sorted(taxa_by_parent_id.get(taxon.id, []), key=sort_key)
        for child in taxon.children:
            add_descendants(child)
        return taxon

    sort_key = sort_key if sort_key is not None else default_sort
    taxa_by_parent_id: Dict[int, List[Taxon]] = sort_groupby(taxa, key=lambda x: x.parent_id or -1)

    root_taxa = taxa_by_parent_id.get(-1, [])
    if len(root_taxa) != 1:
        raise ValueError('Expected exactly one root taxon')

    return add_descendants(root_taxa[0])


def to_rich_tree(taxon: Taxon) -> Tree:
    """Convert a taxon tree to a rich tree"""
    node = Tree(taxon.full_name)
    for child in taxon.children:
        node.add(to_rich_tree(child))
    return node
