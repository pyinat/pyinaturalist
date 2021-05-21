from typing import Dict, List

from attr import define, field, fields_dict

from pyinaturalist.constants import API_V1_BASE_URL
from pyinaturalist.models import BaseModel, Photo, cached_model_property, cached_property, kwarg
from pyinaturalist.node_api import get_taxa_by_id
from pyinaturalist.request_params import RANKS


@define(auto_attribs=False)
class Taxon(BaseModel):
    """A dataclass containing information about a taxon, matching the schema of
    `GET /taxa <https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa>`_.

    Can be constructed from either a full JSON record, a partial JSON record, or just an ID.
    Examples of partial records include nested ``ancestors``, ``children``, and results from
    :py:func:`get_taxa_autocomplete`.
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
    preferred_common_name: str = field(default='')

    # Nested collections
    ancestor_ids: List[int] = field(factory=list)
    conservation_statuses: List[str] = field(factory=list)
    current_synonymous_taxon_ids: List[int] = field(factory=list)
    flag_counts: Dict = field(factory=dict)
    listed_taxa: List = field(factory=list)

    # Lazy-loaded nested model objects
    default_photo: property = cached_model_property(Photo.from_json, '_default_photo')
    _default_photo: Dict = field(factory=dict, repr=False)
    taxon_photos: property = cached_model_property(Photo.from_json_list, '_taxon_photos')
    _taxon_photos: List[Dict] = field(factory=list, repr=False)

    # More model objects, but converters can't be defined here since Taxon isn't created yet
    _ancestors: List[Dict] = field(factory=list, repr=False)
    _ancestors_obj: List['Taxon'] = field(default=None, init=False, repr=False)
    _children: List[Dict] = field(factory=list, repr=False)
    _children_obj: List['Taxon'] = field(default=None, init=False, repr=False)

    # Unused attributes
    # ancestry: str = kwarg

    @cached_property
    def ancestors(self) -> List['Taxon']:
        return self.__class__.from_json_list(self._ancestors) if self._ancestors else []

    @cached_property
    def children(self) -> List['Taxon']:
        if not self._children:
            return []
        # Sort children by rank then name
        children = self.__class__.from_json_list(self._children)
        children.sort(key=get_rank_name_idx)
        return children

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
        for key in fields_dict(self.__class__).keys():
            setattr(self, key, getattr(t, key))


def get_rank_name_idx(taxon):
    return get_rank_idx(taxon.rank), taxon.name


def get_rank_idx(rank: str) -> int:
    return RANKS.index(rank) if rank in RANKS else 0
