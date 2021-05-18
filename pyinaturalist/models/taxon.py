from typing import Dict, List

import attr

from pyinaturalist.constants import API_V1_BASE_URL
from pyinaturalist.models import BaseModel, Photo, kwarg
from pyinaturalist.node_api import get_taxa_by_id
from pyinaturalist.request_params import RANKS


def convert_taxon_photos(taxon_photos):
    return [Photo.from_json(t['photo']) for t in taxon_photos]


@attr.s
class Taxon(BaseModel):
    """A data class containing information about a taxon, matching the schema of ``GET /taxa``
    from the iNaturalist API: https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa

    Can be constructed from either a full JSON record, a partial JSON record, or just an ID.
    Examples of partial records include nested ``ancestors``, ``children``, and results from
    :py:func:`get_taxa_autocomplete`
    """

    ancestry: str = kwarg
    atlas_id: int = kwarg
    complete_rank: str = kwarg
    complete_species_count: int = kwarg
    extinct: bool = kwarg
    iconic_taxon_id: int = kwarg
    iconic_taxon_name: str = kwarg
    id: int = kwarg
    is_active: bool = kwarg
    listed_taxa_count: int = kwarg
    name: str = kwarg
    observations_count: int = kwarg
    parent_id: int = kwarg
    rank: str = kwarg
    rank_level: int = kwarg
    taxon_changes_count: int = kwarg
    taxon_schemes_count: int = kwarg
    wikipedia_summary: str = kwarg
    wikipedia_url: str = kwarg
    preferred_common_name: str = attr.ib(default='')

    # Nested collections with defaults
    ancestor_ids: List[int] = attr.ib(factory=list)
    ancestors: List[Dict] = attr.ib(factory=list)
    children: List[Dict] = attr.ib(factory=list)
    conservation_statuses: List[str] = attr.ib(factory=list)
    current_synonymous_taxon_ids: List[int] = attr.ib(factory=list)
    default_photo: Photo = attr.ib(converter=Photo.from_json, default=None)
    flag_counts: Dict = attr.ib(factory=dict)
    listed_taxa: List = attr.ib(factory=list)
    photos: List[Photo] = attr.ib(init=False, default=None)
    taxon_photos: List[Photo] = attr.ib(converter=convert_taxon_photos, factory=list, repr=False)

    # Internal attrs managed by @properties
    _parent_taxa: List = attr.ib(init=False, default=None)
    _child_taxa: List = attr.ib(init=False, default=None)

    # Add aliases
    # TODO: User properties instead?
    def __attrs_post_init__(self):
        self.photos = self.taxon_photos

    @classmethod
    def from_id(cls, id: int):
        """Lookup and create a new Taxon object from an ID"""
        r = get_taxa_by_id(id)
        return cls.from_json(r['results'][0])

    def update_from_full_record(self):
        t = Taxon.from_id(self.id)
        for key in attr.fields_dict(self.__class__).keys():
            setattr(self, key, getattr(t, key))

    @property
    def ancestry_str(self):
        return ' | '.join(t.name for t in self.parent_taxa)

    @property
    def child_taxa(self) -> List:
        """Get this taxon's children as Taxon objects (in descending order of rank)"""

        def get_child_idx(taxon):
            return get_rank_idx(taxon.rank), taxon.name

        if self._child_taxa is None:
            if not self.children:
                self.update_from_full_record()
            self._child_taxa = [Taxon.from_id(t['id']) for t in self.children]
            # Children may be different ranks; sort children by rank then name
            self._child_taxa.sort(key=get_child_idx)
        return self._child_taxa

    @property
    def parent(self):
        """Return immediate parent, if any"""
        return self.parent_taxa[-1] if self.parent_taxa else None

    @property
    def parent_taxa(self) -> List:
        """Get this taxon's ancestors as Taxon objects (in descending order of rank)"""
        if self._parent_taxa is None:
            if not self.ancestors:
                self.update_from_full_record()
            self._parent_taxa = [Taxon.from_json(t, partial=True) for t in self.ancestors]
        return self._parent_taxa

    @property
    def url(self) -> str:
        return f'{API_V1_BASE_URL}/taxa/{self.id}'


def get_rank_idx(rank: str) -> int:
    return RANKS.index(rank) if rank in RANKS else 0
