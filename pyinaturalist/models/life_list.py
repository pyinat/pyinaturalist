from itertools import groupby
from typing import Dict, List, Optional

from attr import field

from pyinaturalist.constants import ResponseOrFile
from pyinaturalist.models import BaseModel, Taxon, define_model, kwarg, load_json


@define_model
class LifeListTaxon(Taxon):
    """A dataclass containing information about a single taxon in a user's life list"""

    count: int = field(default=0)
    descendant_obs_count: int = field(default=0)
    direct_obs_count: int = field(default=0)

    @property
    def indent_level(self) -> int:
        """Indentation level corresponding to this item's rank level"""
        return int(((70 - self.rank_level) / 5))

    def __str__(self) -> str:
        padding = " " * self.indent_level
        return f'[{self.id:<8}] {padding} {self.rank.title()} {self.name}: {self.count}'


@define_model
class LifeList(BaseModel):
    """A dataclass containing information about a user's life list, based on the schema of
    ``GET /observations/taxonomy``
    """

    count_without_taxon: int = field(default=0)
    taxa: List[LifeListTaxon] = field(factory=list, converter=LifeListTaxon.from_json_list)
    user_id: int = kwarg
    _taxon_counts: Dict[int, int] = field(default=None, init=False, repr=False)

    @classmethod
    def from_json(cls, value: ResponseOrFile, user_id: int = None, **kwargs) -> Optional['LifeList']:
        json_value = load_json(value)
        count_without_taxon = json_value.get('count_without_taxon', 0)
        if 'results' in json_value:
            json_value = json_value['results']

        life_list_json = {'taxa': value, 'user_id': user_id, 'count_without_taxon': count_without_taxon}
        return super(LifeList, cls).from_json(life_list_json)  # type: ignore

    def count(self, taxon_id: int) -> int:
        """Get an observation count for the specified taxon and its descendants.
        **Note:** ``-1`` can be used an alias for ``count_without_taxon``.
        """
        # Make and cache an index of taxon IDs and observation counts
        if self._taxon_counts is None:
            self._taxon_counts = {t.id: t.descendant_obs_count for t in self.taxa}
            self._taxon_counts[-1] = self.count_without_taxon
        return self._taxon_counts.get(taxon_id, 0)

    def tree(self):
        """**Experimental**
        Organize this life list into a taxonomic tree

        Returns:
            :py:class:`rich.tree.Tree`
        """
        return make_tree(self.taxa)

    def __str__(self) -> str:
        return '\n'.join([str(taxon) for taxon in self.taxa])


def make_tree(taxa: List[Taxon]):
    """Organize a list of taxa into a taxonomic tree. Must contain at least one taxon with
    'Life' (taxon ID 48460) as its parent.

    Returns:
        :py:class:`rich.tree.Tree`
    """

    from rich.tree import Tree

    taxa_by_parent_id = _sort_groupby(taxa, key=lambda x: x.parent_id or -1)

    def make_child_tree(node, taxon):
        """Add a taxon and its children to the specified tree node.
        Base case: leaf taxon (with no children)
        Recursive case: non-leaf taxon (with children)
        """
        node = node.add(taxon.full_name)
        for child in taxa_by_parent_id.get(taxon.id, []):
            node.add(make_child_tree(node, child))
        return node

    tree_root = {'id': 48460, 'name': 'Life', 'rank': 'State of matter'}
    return make_child_tree(Tree('life list', expanded=False), Taxon.from_json(tree_root))


def _sort_groupby(values, key):
    """Apply sorting then groupby using the same key"""
    return {k: list(group) for k, group in groupby(sorted(values, key=key), key=key)}
