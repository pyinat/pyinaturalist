import re
from copy import deepcopy
from itertools import chain, groupby
from logging import getLogger
from typing import Any, Callable, Dict, Iterable, List, Optional

from pyinaturalist.constants import (
    GBIF_TAXON_BASE_URL,
    ICONIC_EMOJI,
    ICONIC_TAXA,
    INAT_BASE_URL,
    RANK_EQUIVALENTS,
    RANK_LEVELS,
    RANKS,
    ROOT_TAXON_ID,
    UNRANKED,
    DateTime,
    JsonResponse,
    TableRow,
)
from pyinaturalist.converters import ensure_list
from pyinaturalist.docs import EMOJI
from pyinaturalist.models import (
    BaseModel,
    BaseModelCollection,
    ConservationStatus,
    EstablishmentMeans,
    IconPhoto,
    LazyProperty,
    ListedTaxon,
    Photo,
    datetime_field,
    define_model,
    define_model_collection,
    field,
)

logger = getLogger(__name__)


@define_model
class Taxon(BaseModel):
    """:fa:`dove` An iNaturalist taxon, based on the schema of
    `GET /taxa <https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa>`_.

    Can be constructed from either a full or partial JSON record. Examples of partial records
    include nested ``ancestors``, ``children``, and results from :py:func:`.get_taxa_autocomplete`.
    """

    ancestry: str = field(default=None, doc='Slash-delimited string of ancestor IDs', repr=False)
    ancestor_ids: List[int] = field(
        factory=list,
        converter=ensure_list,  # Handle arrays when converting from a dataframe
        doc='Taxon IDs of ancestors, from highest rank to lowest',
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
        default=None, doc='Name of the iconic taxon (e.g., general taxon "category")'
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
        doc='Number indicating rank level, for easier comparison between ranks (kingdom=highest)',
    )
    reference_url: str = field(default=None, doc='Reference URL for the taxonomy source')
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

    # Indicates this is a partial record (e.g. from nested Taxon.ancestors or children)
    _partial: bool = field(default=False, repr=False)

    # Used for tree formatting
    _indent_level: int = field(default=None, repr=False)

    # Unused attributes
    # atlas_id: int = field(default=None)
    # flag_counts: Dict[str, int] = field(factory=dict)  # {"unresolved": 1, "resolved": 2}
    # min_species_ancestry: str = field(default=None)  # Used internally by iNaturalist for Elasticsearch aggregations
    # min_species_taxon_id: int = field(default=None)
    # photos_locked: bool = field(default=None)
    # universal_search_rank: int = field(default=None)

    def __attrs_post_init__(self):
        # If only ancestor string (or objects) are provided, split into IDs
        if self.ancestry and not self.ancestor_ids:
            delimiter = ',' if ',' in self.ancestry else '/'
            self.ancestor_ids = [int(x) for x in self.ancestry.split(delimiter)]
        elif self.ancestors and not self.ancestor_ids:
            self.ancestor_ids = [t.id for t in self.ancestors]

        # If iconic taxon name is missing, look it up by ID
        if not self.iconic_taxon_name:
            self.iconic_taxon_name = ICONIC_TAXA.get(self.iconic_taxon_id, 'Unknown')

        # If default photo is missing, use iconic taxon icon
        if not self.default_photo:
            self.default_photo = self.icon

        # Normalize rank names
        self.rank = (self.rank or '').lower()
        if self.rank in RANK_EQUIVALENTS:
            self.rank = RANK_EQUIVALENTS[self.rank]

        # If rank level is missing, look it up by name
        if not self.rank_level:
            self.rank_level = RANK_LEVELS.get(self.rank, UNRANKED)

    @classmethod
    def from_sorted_json_list(cls, value: JsonResponse, **kwargs) -> List['Taxon']:
        """Sort Taxon objects by rank then by name"""
        taxa = cls.from_json_list(value, **kwargs)
        taxa.sort(key=_sort_rank_name)
        return taxa

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
        """Taxon rank, scientific name, and common name (if available)"""
        return self._full_name()

    @property
    def rich_full_name(self) -> str:
        """Taxon full name, with italicized scientific name depending on rank (genus and below)"""
        return self._full_name(markup=True)

    def _full_name(self, markup: bool = False) -> str:
        if not self.name and not self.rank:
            return str(self.id)
        if not self.name:
            return f'{self.rank} {self.id}'

        rank = (
            f'{self.rank.title()} '
            if self.rank and self.rank_level > RANK_LEVELS['species']
            else ''
        )
        name = (
            f'[i]{self.name}[/i]'
            if markup and self.rank_level <= RANK_LEVELS['genus']
            else self.name
        )
        common_name = (
            f' ({title(self.preferred_common_name)})' if self.preferred_common_name else ''
        )
        return f'{rank}{name}{common_name}'

    @property
    def icon(self) -> IconPhoto:
        return IconPhoto.from_iconic_taxon(self.iconic_taxon_name)

    @property
    def icon_url(self) -> str:
        """Iconic URL for the icon of the iconic taxon"""
        return str(self.icon.thumbnail_url)

    @property
    def indent_level(self) -> int:
        """Tree indentation level. This may either be manually set, or determined based on rank."""
        if self._indent_level is None:
            self._indent_level = int((RANK_LEVELS['kingdom'] - self.rank_level) / 5) + 1
        return self._indent_level

    @indent_level.setter
    def indent_level(self, value: int):
        self._indent_level = value

    @property
    def gbif_url(self) -> str:
        """URL for the GBIF info page for this taxon"""
        return f'{GBIF_TAXON_BASE_URL}/{self.gbif_id}'

    @property
    def parent(self) -> 'Taxon':
        """Immediate parent, if any"""
        return self.ancestors[-1] if self.ancestors else None

    @property
    def taxonomy(self) -> Dict[str, str]:
        """Ancestor + current taxon as a ``{rank: name}`` dict"""
        return {t.rank: t.name for t in self.ancestors + [self]}

    @property
    def url(self) -> str:
        """Info URL on iNaturalist.org"""
        return f'{INAT_BASE_URL}/taxa/{self.id}'

    def flatten(self, hide_root: bool = False) -> List['Taxon']:
        """Return this taxon and all its descendants as a flat list.
        ``Taxon.indent_level`` is set to indicate the tree depth of each taxon.

        Args:
            hide_root: If True, exclude the current taxon from the list and from indentation level.
        """

        def flatten_tree(taxon: Taxon, level: int = 0) -> List[Taxon]:
            taxon.indent_level = level
            level_taxa = [taxon] if level >= 0 else []

            return level_taxa + list(
                chain.from_iterable(
                    flatten_tree(child, level=level + 1) for child in taxon.children
                )
            )

        return flatten_tree(self, level=-1 if hide_root else 0)

    @property
    def _row(self) -> TableRow:
        return {
            'ID': self.id,
            'Rank': self.rank,
            'Scientific name': f'{self.emoji} {self.name}',
            'Common name': self.preferred_common_name,
        }

    @property
    def _str_attrs(self) -> List[str]:
        return ['id', 'full_name']


# Since these use Taxon classmethods, they must be added after Taxon is defined
Taxon.ancestors = LazyProperty(
    Taxon.from_sorted_json_list,
    name='ancestors',
    type=List[Taxon],
    doc='Ancestor taxa, from highest rank to lowest',
    partial=True,
)
Taxon.children = LazyProperty(
    Taxon.from_sorted_json_list,
    name='children',
    type=List[Taxon],
    doc='Child taxa, sorted by rank then name',
    partial=True,
)

TaxonSortKey = Callable[[Taxon], Any]


@define_model
class TaxonCount(Taxon):
    """:fa:`dove` :fa:`list` A :py:class:`.Taxon` with an associated count, used in a
    :py:class:`.TaxonCounts` collection
    """

    count: int = field(default=0, doc='Number of observations of this taxon')
    descendant_obs_count: int = field(default=0, doc='Number of observations, including children')

    @classmethod
    def from_json(
        cls, value: JsonResponse, user_id: Optional[int] = None, **kwargs
    ) -> 'TaxonCount':
        """Flatten out count + taxon fields into a single-level dict before initializing"""
        if 'taxon' in value:
            value = value.copy()
            value.update(value.pop('taxon'))
        # In life lists, 'count' is aliased as 'direct_obs_count'
        if 'direct_obs_count' in value:
            value['count'] = value.pop('direct_obs_count')
        return super(TaxonCount, cls).from_json(value)

    @property
    def _row(self) -> TableRow:
        return {
            'ID': self.id,
            'Rank': self.rank,
            'Scientific name': f'{self.emoji} {self.name}',
            'Common name': self.preferred_common_name,
            'Count': self.count,
        }

    @property
    def _str_attrs(self) -> List[str]:
        return ['id', 'full_name', 'count']


@define_model_collection
class TaxonCounts(BaseModelCollection):
    """:fa:`dove` :fa:`list` A collection of taxa with an associated counts. Used with
    :v1:`GET /observations/species_counts <Observations/get_observations_species_counts>`.
    as well as :py:class:`.LifeList`.
    """

    data: List[TaxonCount] = field(factory=list, converter=TaxonCount.from_json_list)


@define_model_collection
class LifeList(BaseModelCollection):
    """:fa:`dove` :fa:`list` A user's life list, based on the schema of ``GET /observations/taxonomy``"""

    data: List[TaxonCount] = field(factory=list, converter=TaxonCount.from_json_list)
    count_without_taxon: int = field(default=0, doc='Number of observations without a taxon')
    user_id: int = field(default=None)

    @classmethod
    def from_json(cls, value: JsonResponse, user_id: Optional[int] = None, **kwargs) -> 'LifeList':
        count_without_taxon = value.get('count_without_taxon', 0) if isinstance(value, dict) else 0
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


def title(value: str) -> str:
    """Title case a string, with handling for apostrophes

    Borrowed/modified from ``django.template.defaultfilters.title()``
    """
    return re.sub("([a-z])['’]([A-Z])", lambda m: m[0].lower(), value.title())


def make_tree(
    taxa: Iterable[Taxon],
    include_ranks: Optional[List[str]] = None,
    sort_key: Optional[TaxonSortKey] = None,
    root_id: Optional[int] = None,
) -> Taxon:
    """Organize a list of taxa into a taxonomic tree, defined by ``children`` and ``ancestors``
    attributes. Expects exactly one root taxon.

    Args:
        taxa: Taxon objects to organize
        sort_key: Key function for sorting children; defaults to rank and name
        include_ranks: If provided, only include taxa with these ranks; otherwise, include all ranks
        root_id: ID of the root taxon; if provided, only that taxon and its descendants will
            be included. Otherwise, the root taxon is determined automatically.

    Returns:
        Root taxon of the tree
    """
    include_ranks = [r.lower() for r in include_ranks or []]
    sort_key = sort_key if sort_key is not None else _sort_rank_name
    taxa = [deepcopy(t) for t in taxa]
    root = _find_root(taxa, include_ranks, root_id)

    # Group taxa by parent ID, including any ungrafted children added directly to root
    taxa_by_parent: Dict[int, List[Taxon]] = _sort_groupby(taxa, key=lambda x: x.parent_id or -1)
    if len(root.children) > len(taxa_by_parent.get(root.id, [])):
        taxa_by_parent[root.id] = root.children

    def add_descendants(taxon, ancestors=None) -> Taxon:
        """Recursively add children and ancestors to a taxon"""
        taxon.children = []
        taxon.ancestors = ancestors or []
        for child in get_included_children(taxon):
            child = add_descendants(child, taxon.ancestors + [taxon])
            child.ancestor_ids = [a.id for a in child.ancestors]
            child.parent_id = taxon.id
            taxon.children.append(child)

        taxon.children = sorted(taxon.children, key=sort_key)
        return taxon

    def included(taxon: Taxon) -> bool:
        return not include_ranks or taxon.rank in include_ranks

    def get_included_children(taxon: Taxon) -> List[Taxon]:
        """Get taxon children. If any child ranks are excluded, get the next level of descendants
        that are included."""
        immediate_children = taxa_by_parent.get(taxon.id, [])
        children = [c for c in immediate_children if included(c)]
        for c in [c for c in immediate_children if not included(c)]:
            children.extend(get_included_children(c))
        return children

    return add_descendants(root)


def _find_root(
    taxa: Iterable[Taxon],
    include_ranks: Optional[List[str]] = None,
    root_id: Optional[int] = None,
) -> Taxon:
    """Find the root taxon of a list of taxa, optionally filtering by rank.
    Handles ungrafted and multiple root taxa by adding under a new root node.
    """
    # If a specific root taxon is requested, use that if possible
    if root_id:
        root = next((t for t in taxa if t.id == root_id), None)
        if root and (not include_ranks or root.rank in include_ranks):
            return root
        else:
            logger.warning(f'Root taxon {root_id} not found or filtered out; finding default root')

    # Typical case: exactly one root taxon ("Life")
    taxa_by_id = {t.id: t for t in taxa}
    if ROOT_TAXON_ID in taxa_by_id and (not include_ranks or 'stateofmatter' in include_ranks):
        return taxa_by_id[ROOT_TAXON_ID]
    # Otherwise, find the highest-ranked taxa and graft them under a new root
    else:
        return _find_and_graft_root(taxa, include_ranks)


def _find_and_graft_root(taxa: Iterable[Taxon], include_ranks: Optional[List[str]] = None) -> Taxon:
    taxa_by_id = {t.id: t for t in taxa}
    max_rank = max(t.rank_level for t in taxa if not include_ranks or t.rank in include_ranks)
    root_taxa = [t for t in taxa if t.rank_level == max_rank]

    # Add any ungrafted taxa and deduplicate
    ungrafted = [
        t
        for t in taxa
        if t.parent_id not in taxa_by_id and (not include_ranks or t.rank in include_ranks)
    ]
    root_taxa = list({t.id: t for t in root_taxa + ungrafted}.values())

    if len(root_taxa) == 1:
        return root_taxa[0]

    # If there are multiple branches, we need to insert a 'Life' root above them
    root = TaxonCount(id=ROOT_TAXON_ID, name='Life', rank='stateofmatter', is_active=True)  # type: ignore
    root.children = root_taxa
    for t in root.children:
        t.ancestors = [root]
        t.ancestor_ids = [root.id]
        t.parent_id = root.id
    return root


def _sort_groupby(values, key):
    """Apply sorting then grouping using the same key"""
    return {k: list(group) for k, group in groupby(sorted(values, key=key), key=key)}


def _sort_rank_name(taxon):
    """Get a sort key by rank (descending) and name"""
    return (taxon.rank_level or 0) * -1, taxon.name
