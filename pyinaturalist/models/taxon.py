from datetime import datetime
from typing import Any, Dict, List, Optional

from attr import field, fields_dict

from pyinaturalist.constants import (
    ICONIC_EMOJI,
    ICONIC_TAXA_BASE_URL,
    INAT_BASE_URL,
    RANKS,
    JsonResponse,
    TableRow,
)
from pyinaturalist.models import BaseModel, LazyProperty, Photo, datetime_attr, define_model, kwarg
from pyinaturalist.v1 import get_taxa_by_id


@define_model
class Taxon(BaseModel):
    """An iNaturalist taxon, based on the schema of
    `GET /taxa <https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa>`_.

    Can be constructed from either a full or partial JSON record. Examples of partial records
    include nested ``ancestors``, ``children``, and results from :py:func:`.get_taxa_autocomplete`.
    """

    complete_rank: str = kwarg  #: Complete or "leaf taxon" rank, e.g. species or subspecies
    complete_species_count: int = kwarg  #: Total number of species descended from this taxon
    created_at: Optional[datetime] = datetime_attr  #: When the taxon was added to iNaturalist
    extinct: bool = kwarg  #: Indicates if the taxon is extinct
    iconic_taxon_id: int = field(default=0)  #: ID of the iconic taxon or taxon "category"
    iconic_taxon_name: str = field(default='unknown')  #: Name of the iconic taxon or taxon "category"
    id: int = kwarg  #: Taxon ID
    is_active: bool = kwarg  #: Indicates if the taxon is active (and not renamed, moved, etc.)
    listed_taxa_count: int = kwarg  #: Number of listed taxa from this taxon + descendants
    name: str = kwarg  #: Taxon name; contains full scientific name at species level and below
    observations_count: int = kwarg  #: Total number of observations of this taxon and its descendants
    parent_id: int = kwarg  #: Taxon ID of immediate ancestor
    preferred_common_name: str = field(default='')  #: Common name for the preferred place, if any
    preferred_establishment_means: str = kwarg  #: Establishment means for this taxon + preferred place
    rank_level: int = kwarg  #: Rank number for easier comparison between ranks (kingdom=higest)
    rank: str = kwarg  #: Taxon rank (species, genus, etc.)
    taxon_changes_count: int = kwarg  #: Number of curator changes to this taxon
    taxon_schemes_count: int = kwarg  #: Taxon schemes that include this taxon
    wikipedia_summary: str = kwarg  #: Taxon summary from Wikipedia article, if available
    wikipedia_url: str = kwarg  #: URL to Wikipedia article for the taxon, if available

    # Nested collections
    # TODO: Models+enums for conservation status and establishment means?
    ancestor_ids: List[int] = field(factory=list)  #: Taxon IDs of ancestors, from highest rank to lowest
    conservation_status: Dict[str, Any] = field(factory=dict)
    conservation_statuses: List[Dict] = field(factory=list)  #:
    current_synonymous_taxon_ids: List[int] = field(factory=list)  #: Taxa that are accepted synonyms
    establishment_means: Dict[str, Any] = field(factory=dict)  #: Establishment means details
    listed_taxa: List = field(factory=list)  #: Listed taxon IDs

    # Lazy-loaded nested model objects
    ancestors: property = LazyProperty(BaseModel.from_json_list)
    children: property = LazyProperty(BaseModel.from_json_list)
    default_photo: property = LazyProperty(Photo.from_json)
    taxon_photos: property = LazyProperty(Photo.from_json_list)

    # Unused attributes
    # atlas_id: int = kwarg
    # flag_counts: Dict[str, int] = field(factory=dict)  # {"unresolved": 1, "resolved": 2}
    # min_species_ancestry: str = kwarg  #: Used internally by iNaturalist for Elasticsearch aggregations
    # min_species_taxon_id: int = kwarg
    # photos_locked: bool = kwarg
    # universal_search_rank: int = kwarg

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
    def full_name(self) -> str:
        """Taxon rank, scientific name, and common name (if available).

        Example:

            >>> taxon.full_name
            'Genus: Physcia (Rosette Lichens)'

        """
        if not self.name and not self.rank:
            return 'unknown taxon'
        if not self.name:
            name = str(self.id)
        else:
            common_name = self.preferred_common_name
            name = self.name + (f' ({common_name})' if common_name else '')

        return f'{self.rank.title()}: {name}'

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

    @property
    def row(self) -> TableRow:
        return {
            'ID': self.id,
            'Rank': self.rank,
            'Scientific name': f'{self.emoji} {self.name}',
            'Common name': self.preferred_common_name,
        }

    def __str__(self) -> str:
        return f'[{self.id}] {self.full_name}' if self.name else self.full_name


# Since these use Taxon classmethods, they must be added after Taxon is defined
Taxon.ancestors = LazyProperty(Taxon.from_json_list, 'ancestors')
Taxon.children = LazyProperty(Taxon.from_sorted_json_list, 'children')


@define_model
class TaxonCount(Taxon):
    """A taxon with an associated count, used in a :py:class:`.TaxonCounts` collection"""

    count: int = field(default=0)

    @classmethod
    def from_json(cls, value: JsonResponse, user_id: int = None, **kwargs) -> 'TaxonCount':
        """Flatten out count + taxon fields into a single-level dict before initializing"""
        if 'results' in value:
            value = value['results']
        if 'taxon' in value:
            value.update(value.pop('taxon'))
        return super(TaxonCount, cls).from_json(value)  # type: ignore

    @property
    def row(self) -> TableRow:
        return {
            'ID': self.id,
            'Rank': self.rank,
            'Name': self.name,
            'Count': self.count,
        }

    def __str__(self) -> str:
        return f'[{self.id}] {self.full_name}: {self.count}'


@define_model
class TaxonCounts(BaseModel):
    """A taxon with an associated count. Used with
    `GET /observations/species_counts <https://api.inaturalist.org/v1/docs/#!/Observations/get_observations_species_counts>`_.
    as well as :py:class:`.LifeList`.
    """

    taxa: List[TaxonCount] = field(factory=list, converter=TaxonCount.from_json_list)
    _taxon_counts: Dict[int, int] = field(default=None, init=False, repr=False)

    @classmethod
    def from_json(cls, value: JsonResponse, **kwargs) -> 'TaxonCounts':
        if 'results' in value:
            value = value['results']
        if 'taxa' not in value:
            value = {'taxa': value}
        return super(TaxonCounts, cls).from_json(value)  # type: ignore

    @classmethod
    def from_json_list(cls, value: JsonResponse, **kwargs) -> 'TaxonCounts':  # type: ignore
        """Since this model represents a collection, just alias this to ``from_json``"""
        return cls.from_json(value)

    def count(self, taxon_id: int) -> int:
        """Get an observation count for the specified taxon and its descendants.
        **Note:** ``-1`` can be used an alias for ``count_without_taxon``.
        """
        # Make and cache an index of taxon IDs and observation counts
        if self._taxon_counts is None:
            self._taxon_counts = {t.id: t.descendant_obs_count for t in self.taxa}
            self._taxon_counts[-1] = self.count_without_taxon
        return self._taxon_counts.get(taxon_id, 0)

    def __str__(self) -> str:
        return '\n'.join([str(taxon) for taxon in self.taxa])


def _get_rank_name_idx(taxon):
    return _get_rank_idx(taxon.rank), taxon.name


def _get_rank_idx(rank: str) -> int:
    return RANKS.index(rank) if rank in RANKS else 0
