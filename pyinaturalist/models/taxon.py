from typing import Dict, List

from attr import field, fields_dict

from pyinaturalist.constants import ICONIC_EMOJI, ICONIC_TAXA_BASE_URL, INAT_BASE_URL, JsonResponse
from pyinaturalist.models import BaseModel, LazyProperty, Photo, define_model, kwarg
from pyinaturalist.request_params import RANKS
from pyinaturalist.v1 import get_taxa_by_id


@define_model
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
    iconic_taxon_id: int = field(default=0)
    iconic_taxon_name: str = field(default='unknown')
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
    ancestors: property = LazyProperty(BaseModel.from_json_list)
    children: property = LazyProperty(BaseModel.from_json_list)
    default_photo: property = LazyProperty(Photo.from_json)
    taxon_photos: property = LazyProperty(Photo.from_json_list)

    @classmethod
    def from_sorted_json_list(cls, value: JsonResponse) -> List['Taxon']:
        """Sort Taxon objects by rank then by name"""
        taxa = cls.from_json_list(value)
        taxa.sort(key=_get_rank_name_idx)
        return taxa  # type: ignore

    @property
    def ancestry(self) -> str:
        """String containing either ancestor names (if available) or IDs"""
        tokens = [t.name for t in self.ancestors] if self.ancestors else self.ancestor_ids
        return ' | '.join([str(t) for t in tokens])

    @property
    def emoji(self) -> str:
        """Get an emoji representing the iconic taxon"""
        return ICONIC_EMOJI.get(self.iconic_taxon_id, '❓')

    @property
    def full_name(taxon) -> str:
        """Taxon rank, scientific name, and common name (if available)"""
        if not taxon:
            return 'unknown taxon'
        if not taxon.name:
            name = str(taxon.id)
        else:
            common_name = taxon.preferred_common_name
            name = taxon.name + (f' ({common_name})' if common_name else '')

        return f'{taxon.rank.title()}: {name}'

    @property
    def icon_url(self) -> str:
        """Get a URL to the iconic taxon's icon"""
        return f'{ICONIC_TAXA_BASE_URL}/{self.iconic_taxon_name.lower()}-75px.png'

    @property
    def parent(self) -> 'Taxon':
        """Get immediate parent, if any"""
        return self.ancestors[-1] if self.ancestors else None

    @property
    def url(self) -> str:
        """Info URL on iNaturalist.org"""
        return f'{INAT_BASE_URL}/taxa/{self.id}'

    @classmethod
    def from_id(cls, id: int) -> 'Taxon':
        """Lookup and create a new Taxon object by ID"""
        r = get_taxa_by_id(id)
        return cls.from_json(r['results'][0])  # type: ignore

    def load_full_record(self):
        """Update this Taxon with full taxon info, including ancestors + children"""
        t = Taxon.from_id(self.id)
        for key in fields_dict(Taxon).keys():
            key = key.lstrip('_')  # Use getters/setters for LazyProperty instead of temp attrs
            setattr(self, key, getattr(t, key))

    # Column headers for simplified table format
    headers = {
        'ID': 'cyan',
        'Rank': 'dodger_blue1',
        'Scientific name': 'green',
        'Common name': 'blue',
    }

    @property
    def row(self) -> List:
        """Get basic values to display as a row in a table"""
        return [self.id, self.rank, f'{self.emoji} {self.name}', self.preferred_common_name]

    def __str__(self) -> str:
        return f'[{self.id}] {self.full_name}' if self.name else self.full_name


# Since these use Taxon classmethods, they must be added after Taxon is defined
Taxon.ancestors = LazyProperty(Taxon.from_json_list, 'ancestors')
Taxon.children = LazyProperty(Taxon.from_sorted_json_list, 'children')


def _get_rank_name_idx(taxon):
    return _get_rank_idx(taxon.rank), taxon.name


def _get_rank_idx(rank: str) -> int:
    return RANKS.index(rank) if rank in RANKS else 0
