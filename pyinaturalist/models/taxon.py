from typing import Dict, List

from attr import fields_dict

from pyinaturalist.constants import (
    CONSERVATION_STATUSES,
    ESTABLISTMENT_MEANS,
    ICONIC_EMOJI,
    ICONIC_TAXA_BASE_URL,
    INAT_BASE_URL,
    RANKS,
    DateTime,
    JsonResponse,
    TableRow,
)
from pyinaturalist.models import (
    BaseModel,
    BaseModelCollection,
    LazyProperty,
    Photo,
    Place,
    User,
    datetime_field,
    define_model,
    define_model_collection,
    field,
    is_in,
    upper,
)
from pyinaturalist.v1 import get_taxa_by_id


# TODO: Some more properties to consolidate differences between endpoints? (place_id vs. place, etc.)
# TODO: Include codes from other sources? Currently only including IUCN codes.
@define_model
class ConservationStatus(BaseModel):
    """The conservation status of a taxon in a given location, based on the schema of:

    * Taxon.conservation_status from `GET /taxa <https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa>`_
    * Observation.taxon.conservation_statused from `GET /observations <https://api.inaturalist.org/v1/docs/#!/Observations/get_observations>`_
    """

    authority: str = field(default=None, doc='Data source for conservation status')
    created_at: DateTime = datetime_field(doc='Date and time the conservation status was created')
    description: str = field(default=None, doc='Description of conservation status')
    geoprivacy: str = field(
        default=None, doc='Default geoprivacy level; may be obscured or private for protected species'
    )
    iucn: int = field(default=None, doc='IUCD ID, if applicable')
    place_id: int = field(default=None)
    source_id: int = field(default=None)
    status: str = field(
        default=None,
        converter=upper,
        validator=is_in(CONSERVATION_STATUSES),
        doc='Short code for conservation status',
    )
    status_name: str = field(default=None, doc='Full name of conservation status')
    taxon_id: int = field(default=None, doc='Taxon ID')
    updated_at: DateTime = datetime_field(doc='Date and time the conservation status was last updated')
    updater_id: int = field(default=None)
    url: str = field(default=None, doc='Link to data source with more details')

    # Lazy-loaded nested model objects
    place: property = LazyProperty(Place.from_json)
    updater: property = LazyProperty(User.from_json)
    user: property = LazyProperty(User.from_json)


@define_model
class EstablishmentMeans(BaseModel):
    """The establishment means for a taxon in a given location"""

    establishment_means: str = field(
        default=None, validator=is_in(ESTABLISTMENT_MEANS), doc='Establishment means description'
    )
    place: property = LazyProperty(Place.from_json_list)

    def __str__(self) -> str:
        return self.establishment_means


@define_model
class Taxon(BaseModel):
    """An iNaturalist taxon, based on the schema of
    `GET /taxa <https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa>`_.

    Can be constructed from either a full or partial JSON record. Examples of partial records
    include nested ``ancestors``, ``children``, and results from :py:func:`.get_taxa_autocomplete`.
    """

    complete_rank: str = field(
        default=None, doc='Complete or "leaf taxon" rank, e.g. species or subspecies'
    )
    complete_species_count: int = field(
        default=None, doc='Total number of species descended from this taxon'
    )
    created_at: DateTime = datetime_field(doc='Date and time the taxon was added to iNaturalist')
    extinct: bool = field(default=None, doc='Indicates if the taxon is extinct')
    iconic_taxon_id: int = field(
        default=0, doc='ID of the iconic taxon (e.g., general taxon "category")'
    )
    iconic_taxon_name: str = field(
        default='unknown', doc='Name of the iconic taxon (e.g., general taxon "category")'
    )
    is_active: bool = field(
        default=None, doc='Indicates if the taxon is active (and not renamed, moved, etc.)'
    )
    listed_taxa_count: int = field(
        default=None, doc='Number of listed taxa from this taxon + descendants'
    )
    name: str = field(
        default=None, doc='Taxon name; contains full scientific name at species level and below'
    )
    observations_count: int = field(
        default=None, doc='Total number of observations of this taxon and its descendants'
    )
    parent_id: int = field(default=None, doc='Taxon ID of immediate ancestor')
    preferred_common_name: str = field(default='', doc='Common name for the preferred place, if any')
    preferred_establishment_means: str = field(
        default=None, doc='Establishment means for this taxon in the given preferred place (if any)'
    )
    rank_level: int = field(
        default=None,
        doc='Number indicating rank level, for easier comparison between ranks (kingdom=higest)',
    )
    rank: str = field(default=None, validator=is_in(RANKS), doc='Taxon rank')
    taxon_changes_count: int = field(default=None, doc='Number of curator changes to this taxon')
    taxon_schemes_count: int = field(default=None, doc='Taxon schemes that include this taxon')
    wikipedia_summary: str = field(
        default=None, doc='Taxon summary from Wikipedia article, if available'
    )
    wikipedia_url: str = field(default=None, doc=' URL to Wikipedia article for the taxon, if available')

    # Nested collections
    ancestor_ids: List[int] = field(
        factory=list, doc='Taxon IDs of ancestors, from highest rank to lowest'
    )
    current_synonymous_taxon_ids: List[int] = field(
        factory=list, doc='Taxon IDs of taxa that are accepted synonyms'
    )
    listed_taxa: List[int] = field(factory=list, doc='Listed taxon IDs')

    # Lazy-loaded nested model objects
    ancestors: property = LazyProperty(BaseModel.from_json_list)
    children: property = LazyProperty(BaseModel.from_json_list)
    conservation_status: property = LazyProperty(ConservationStatus.from_json)
    conservation_statuses: property = LazyProperty(ConservationStatus.from_json_list)
    default_photo: property = LazyProperty(Photo.from_json)
    establishment_means: property = LazyProperty(EstablishmentMeans.from_json)
    taxon_photos: property = LazyProperty(Photo.from_json_list)

    # Unused attributes
    # atlas_id: int = field(default=None)
    # flag_counts: Dict[str, int] = field(factory=dict)  # {"unresolved": 1, "resolved": 2}
    # min_species_ancestry: str = field(default=None)  #: Used internally by iNaturalist for Elasticsearch aggregations
    # min_species_taxon_id: int = field(default=None)
    # partial: bool = field(default=None, repr=False)
    # photos_locked: bool = field(default=None)
    # universal_search_rank: int = field(default=None)

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
    def child_ids(self) -> List[int]:
        """Taxon IDs of direct children, sorted by rank then name"""
        return [t.id for t in self.children]

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


@define_model
class TaxonCount(Taxon):
    """A taxon with an associated count, used in a :py:class:`.TaxonCounts` collection"""

    count: int = field(default=0)  #: Number of observations of this taxon

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


@define_model_collection
class TaxonCounts(BaseModelCollection):
    """A collection of taxa with an associated counts. Used with
    `GET /observations/species_counts <https://api.inaturalist.org/v1/docs/#!/Observations/get_observations_species_counts>`_.
    as well as :py:class:`.LifeList`.
    """

    data: List[TaxonCount] = field(factory=list, converter=TaxonCount.from_json_list)
    _taxon_counts: Dict[int, int] = field(default=None, init=False, repr=False)

    def count(self, taxon_id: int) -> int:
        """Get an observation count for the specified taxon and its descendants, and handle unlisted taxa.
        **Note:** ``-1`` can be used an alias for ``count_without_taxon``.
        """
        # Make and cache an index of taxon IDs and observation counts
        if self._taxon_counts is None:
            self._taxon_counts = {t.id: t.descendant_obs_count for t in self.data}
            self._taxon_counts[-1] = self.count_without_taxon
        return self._taxon_counts.get(taxon_id, 0)

    def __str__(self) -> str:
        return '\n'.join([str(taxon) for taxon in self.data])


# Since these use Taxon classmethods, they must be added after Taxon is defined
Taxon.ancestors = LazyProperty(Taxon.from_json_list, 'ancestors')
Taxon.children = LazyProperty(Taxon.from_sorted_json_list, 'children')


def _get_rank_name_idx(taxon):
    return _get_rank_idx(taxon.rank), taxon.name


def _get_rank_idx(rank: str) -> int:
    return RANKS.index(rank) if rank in RANKS else 0
