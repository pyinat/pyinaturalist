from typing import Dict, List

import attr

from pyinaturalist.constants import API_V1_BASE_URL
from pyinaturalist.models import BaseModel, Photo, cached_property, dataclass, kwarg
from pyinaturalist.node_api import get_taxa_by_id
from pyinaturalist.request_params import RANKS


@dataclass
class Taxon(BaseModel):
    """A dataclass containing information about a taxon, matching the schema of
    `GET /taxa <https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa>`_.

    Can be constructed from either a full JSON record, a partial JSON record, or just an ID.
    Examples of partial records include nested ``ancestors``, ``children``, and results from
    :py:func:`get_taxa_autocomplete`
    """

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

    # Lazy-loaded nested model objects
    _ancestors: List[Dict] = attr.ib(factory=list, repr=False)
    _children: List[Dict] = attr.ib(factory=list, repr=False)
    _default_photo: Dict = attr.ib(factory=dict, repr=False)
    _taxon_photos: List[Dict] = attr.ib(factory=list, repr=False)
    _ancestors_obj: List['Taxon'] = None  # type: ignore
    _children_obj: List['Taxon'] = None  # type: ignore
    _default_photo_obj: Photo = None  # type: ignore
    _taxon_photos_obj: List[Photo] = None  # type: ignore

    # Nested collections
    ancestor_ids: List[int] = attr.ib(factory=list)
    conservation_statuses: List[str] = attr.ib(factory=list)
    current_synonymous_taxon_ids: List[int] = attr.ib(factory=list)
    flag_counts: Dict = attr.ib(factory=dict)
    listed_taxa: List = attr.ib(factory=list)

    # Unused attributes
    # ancestry: str = kwarg

    @cached_property
    def ancestors(self) -> List['Taxon']:
        return self.__class__.from_json_list(self._ancestors)

    @cached_property
    def children(self) -> List['Taxon']:
        # Sort children by rank then name
        children = self.__class__.from_json_list(self._children)
        children.sort(key=get_rank_name_idx)
        return children

    @cached_property
    def default_photo(self) -> Photo:
        return Photo.from_json(self._default_photo)

    @cached_property
    def taxon_photos(self) -> List[Photo]:
        return Photo.from_json_list([t['photo'] for t in self._taxon_photos])

    @property
    def ancestry(self):
        tokens = [t.name for t in self.ancestors] if self.ancestors else self.ancestor_ids
        if self.ancestors:
            return ' | '.join(tokens)

    @property
    def parent(self):
        """Return immediate parent, if any"""
        return self.ancestors[-1] if self.ancestors else None

    @property
    def url(self) -> str:
        return f'{API_V1_BASE_URL}/taxa/{self.id}'

    @classmethod
    def from_id(cls, id: int):
        """Lookup and create a new Taxon object by ID"""
        r = get_taxa_by_id(id)
        return cls.from_json(r['results'][0])

    def update_from_full_record(self):
        t = Taxon.from_id(self.id)
        for key in attr.fields_dict(self.__class__).keys():
            setattr(self, key, getattr(t, key))


def get_rank_name_idx(taxon):
    return get_rank_idx(taxon.rank), taxon.name


def get_rank_idx(rank: str) -> int:
    return RANKS.index(rank) if rank in RANKS else 0
