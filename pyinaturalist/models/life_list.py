from typing import Dict, List, Optional

from attr import field

from pyinaturalist.constants import ResponseOrFile
from pyinaturalist.models import BaseModel, define_model, kwarg, load_json


@define_model
class LifeListTaxon(BaseModel):
    """A dataclass containing information about a single taxon in a user's life list"""

    count: int = kwarg
    descendant_obs_count: int = kwarg
    direct_obs_count: int = kwarg
    id: int = kwarg
    is_active: bool = kwarg
    name: str = kwarg
    parent_id: int = kwarg
    rank_level: int = kwarg
    rank: str = kwarg  # Enum


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

    # TODO: Restructure flat taxonomy list into a tree, based on parent_id
    # def tree(self):
    #     pass
