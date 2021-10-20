from typing import Dict, List

from attr import fields_dict

from pyinaturalist.constants import (
    ICONIC_EMOJI,
    ICONIC_TAXA_BASE_URL,
    INAT_BASE_URL,
    RANKS,
    DateTime,
    JsonResponse,
    TableRow,
)
from pyinaturalist.docs import EMOJI
from pyinaturalist.models import (
    BaseModel,
    BaseModelCollection,
    ConservationStatus,
    EstablishmentMeans,
    LazyProperty,
    ListedTaxon,
    Photo,
    datetime_field,
    define_model,
    define_model_collection,
    field,
)


@define_model
class Taxon(BaseModel):
    """:fa:`dove,style=fas` An iNaturalist taxon, based on the schema of
    `GET /taxa <https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa>`_.

    Can be constructed from either a full or partial JSON record. Examples of partial records
    include nested ``ancestors``, ``children``, and results from :py:func:`.get_taxa_autocomplete`.
    """

    ancestor_ids: List[int] = field(
        factory=list, doc='Taxon IDs of ancestors, from highest rank to lowest'
    )
    complete_rank: str = field(
        default=None, doc='Complete or "leaf taxon" rank, e.g. species or subspecies'
    )
    complete_species_count: int = field(
        default=None, doc='Total number of species descended from this taxon'
    )
    created_at: DateTime = datetime_field(doc='Date and time the taxon was added to iNaturalist')
    current_synonymous_taxon_ids: List[int] = field(
        factory=list, doc='Taxon IDs of taxa that are accepted synonyms'
    )
    extinct: bool = field(default=None, doc='Indicates if the taxon is extinct')
    gbif_id: int = field(default=None, doc='GBIF taxon ID')
    iconic_taxon_id: int = field(
        default=0, doc='ID of the iconic taxon (e.g., general taxon "category")'
    )
    iconic_taxon_name: str = field(
        default='unknown', doc='Name of the iconic taxon (e.g., general taxon "category")'
    )
    is_active: bool = field(
        default=None, doc='Indicates if the taxon is active (and not renamed, moved, etc.)'
    )
    listed_places: bool = field(
        default=None, doc='Indicates if there are listed places for this taxon'
    )
    listed_taxa_count: int = field(
        default=None, doc='Number of listed taxa from this taxon + descendants'
    )
    matched_term: str = field(default=None, doc='Matched search term, from autocomplete results')
    name: str = field(
        default=None, doc='Taxon name; contains full scientific name at species level and below'
    )
    names: List[Dict] = field(
        factory=list, doc='All regional common names; only returned if ``all_names`` is specified'
    )
    observations_count: int = field(
        default=None, doc='Total number of observations of this taxon and its descendants'
    )
    parent_id: int = field(default=None, doc='Taxon ID of immediate ancestor')
    preferred_common_name: str = field(
        default='', doc='Common name for the preferred place, if any'
    )
    preferred_establishment_means: str = field(
        default=None, doc='Establishment means for this taxon in the given preferred place (if any)'
    )
    rank_level: int = field(
        default=None,
        doc='Number indicating rank level, for easier comparison between ranks (kingdom=higest)',
    )
    ranges: bool = field(default=None, doc='Indicates if there is range data for this taxon')
    rank: str = field(default=None, options=RANKS, doc='Taxon rank')
    taxon_changes_count: int = field(default=None, doc='Number of curator changes to this taxon')
    taxon_schemes_count: int = field(default=None, doc='Taxon schemes that include this taxon')
    vision: bool = field(
        default=None, doc='Indicates if this taxon is included in the computer vision model'
    )
    wikipedia_summary: str = field(default=None, doc='Taxon summary from Wikipedia article')
    wikipedia_url: str = field(default=None, doc='URL to Wikipedia article for the taxon')

    # Lazy-loaded model objects
    ancestors: property = LazyProperty(BaseModel.from_json_list)
    children: property = LazyProperty(BaseModel.from_json_list)
    conservation_status: property = LazyProperty(
        ConservationStatus.from_json,
        type=ConservationStatus,
        doc='Conservation status of the taxon in a given location',
    )
    conservation_statuses: property = LazyProperty(
        ConservationStatus.from_json_list,
        type=List[ConservationStatus],
        doc='Conservation statuses of the taxon in different locations',
    )
    default_photo: property = LazyProperty(Photo.from_json, type=Photo, doc='Taxon default photo')
    establishment_means: property = LazyProperty(
        EstablishmentMeans.from_json,
        type=EstablishmentMeans,
        doc='Establishment means for a taxon in a given location',
    )
    listed_taxa: property = LazyProperty(
        ListedTaxon.from_json_list,
        type=List[ListedTaxon],
        doc='Details about this taxon associated with a list',
    )
    taxon_photos: property = LazyProperty(
        Photo.from_json_list, type=List[Photo], doc='All taxon photos shown on taxon info page'
    )

    # Unused attributes
    # atlas_id: int = field(default=None)
    # flag_counts: Dict[str, int] = field(factory=dict)  # {"unresolved": 1, "resolved": 2}
    # min_species_ancestry: str = field(default=None)  # Used internally by iNaturalist for Elasticsearch aggregations
    # min_species_taxon_id: int = field(default=None)
    # partial: bool = field(default=None, repr=False)
    # photos_locked: bool = field(default=None)
    # universal_search_rank: int = field(default=None)

    @classmethod
    def from_sorted_json_list(cls, value: JsonResponse) -> List['Taxon']:
        """Sort Taxon objects by rank then by name"""
        taxa = cls.from_json_list(value)
        taxa.sort(key=_get_rank_name_idx)
        return taxa

    @property
    def ancestry(self) -> str:
        """String containing either ancestor names (if available) or IDs"""
        tokens = [t.name for t in self.ancestors] if self.ancestors else self.ancestor_ids
        return ' | '.join([str(t) for t in tokens])

    @property
    def child_ids(self) -> List[int]:
        """Taxon IDs of direct children, sorted by rank then name"""
        return [t.id for t in self.children]

    @property
    def emoji(self) -> str:
        """Get an emoji representing the taxon"""
        for taxon_id in [self.id] + list(reversed(self.ancestor_ids)):
            if taxon_id in EMOJI:
                return EMOJI[taxon_id]
        return ICONIC_EMOJI.get(self.iconic_taxon_id, '❓')

    @property
    def full_name(self) -> str:
        """Taxon rank, scientific name, common name (if available), and emoji"""
        if not self.name and not self.rank:
            return 'unknown taxon'
        if not self.name:
            return f'{self.rank.title()}: {self.id}'

        common_name = f' ({self.preferred_common_name})' if self.preferred_common_name else ''
        return f'{self.emoji} {self.rank.title()}: {self.name}{common_name}'

    @property
    def icon_url(self) -> str:
        """URL for the iconic taxon's icon"""
        return f'{ICONIC_TAXA_BASE_URL}/{self.iconic_taxon_name.lower()}-75px.png'

    @property
    def gbif_url(self) -> str:
        """URL for the GBIF info page for this taxon"""
        return f'https://www.gbif.org/species/{self.gbif_id}'

    @property
    def parent(self) -> 'Taxon':
        """Immediate parent, if any"""
        return self.ancestors[-1] if self.ancestors else None

    @property
    def url(self) -> str:
        """Info URL on iNaturalist.org"""
        return f'{INAT_BASE_URL}/taxa/{self.id}'

    @classmethod
    def from_id(cls, id: int) -> 'Taxon':
        """Lookup and create a new Taxon object by ID"""
        from pyinaturalist.v1 import get_taxa_by_id

        r = get_taxa_by_id(id)
        return cls.from_json(r['results'][0])

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


@define_model
class TaxonCount(Taxon):
    """:fa:`dove,style=fas` :fa:`list` A :py:class:`.Taxon` with an associated count, used in a
    :py:class:`.TaxonCounts` collection
    """

    count: int = field(default=0, doc='Number of observations of this taxon')

    @classmethod
    def from_json(cls, value: JsonResponse, user_id: int = None, **kwargs) -> 'TaxonCount':
        """Flatten out count + taxon fields into a single-level dict before initializing"""
        if 'results' in value:
            value = value['results']
        if 'taxon' in value:
            value = value.copy()
            value.update(value.pop('taxon'))
        return super(TaxonCount, cls).from_json(value)

    @property
    def row(self) -> TableRow:
        return {
            'ID': self.id,
            'Rank': self.rank,
            'Scientific name': f'{self.emoji} {self.name}',
            'Common name': self.preferred_common_name,
            'Count': self.count,
        }

    def __str__(self) -> str:
        return f'[{self.id}] {self.full_name}: {self.count}'


@define_model_collection
class TaxonCounts(BaseModelCollection):
    """:fa:`dove,style=fas` :fa:`list` A collection of taxa with an associated counts. Used with
    :v1:`GET /observations/species_counts <Observations/get_observations_species_counts>`.
    as well as :py:class:`.LifeList`.
    """

    data: List[TaxonCount] = field(factory=list, converter=TaxonCount.from_json_list)


# Since these use Taxon classmethods, they must be added after Taxon is defined
Taxon.ancestors = LazyProperty(
    Taxon.from_sorted_json_list,
    name='ancestors',
    type=List[Taxon],
    doc='Ancestor taxa, from highest rank to lowest',
)
Taxon.children = LazyProperty(
    Taxon.from_sorted_json_list,
    name='children',
    type=List[Taxon],
    doc='Child taxa, sorted by rank then name',
)


def _get_rank_name_idx(taxon):
    """Sort index by rank and name (ascending)"""
    idx = RANKS.index(taxon.rank) if taxon.rank in RANKS else 0
    return idx * -1, taxon.name
