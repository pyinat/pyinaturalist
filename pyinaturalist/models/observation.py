import math
from datetime import datetime
from itertools import chain
from typing import Any

from pyinaturalist.constants import (
    ALL_LICENSES,
    GEOPRIVACY_LEVELS,
    HISTOGRAM_INTERVALS,
    INAT_BASE_URL,
    QUALITY_GRADES,
    Coordinates,
    DateOrInt,
    DateTime,
    HistogramResponse,
    JsonResponse,
    TableRow,
)
from pyinaturalist.converters import convert_histogram, get_histogram_interval
from pyinaturalist.docs import extend_init_signature
from pyinaturalist.models import (
    Annotation,
    BaseModel,
    BaseModelCollection,
    Comment,
    IconPhoto,
    Identification,
    LazyProperty,
    ObservationFieldValue,
    Photo,
    ProjectObservation,
    Sound,
    Taxon,
    User,
    coordinate_pair,
    datetime_field,
    datetime_now_field,
    define_model,
    define_model_collection,
    define_model_custom_init,
    field,
    upper,
)


@define_model
class Application(BaseModel):
    """:fa:`display` An iNaturalist mobile or third-party application"""

    icon: str = field(default=None, doc='Application icon URL')
    name: str = field(default=None, doc='Application name')
    url: str = field(default=None, doc='Application URL')

    @property
    def _str_attrs(self) -> list[str]:
        return ['id', 'name', 'url']


@define_model
class Flag(BaseModel):
    """:fa:`flag` A flag on an observation"""

    comment = field(default=None, doc='Flag comment')
    created_at: datetime = datetime_field(doc='Date and time the flag was created')
    flag: str = field(default=None, doc='Flag type')
    flaggable_content: str = field(default=None)
    flaggable_id: int = field(default=None)
    flaggable_type: str = field(default=None)
    flaggable_user_id: int = field(default=None)
    resolved: bool = field(default=None)
    resolver_id: int = field(default=None)
    resolved_at: datetime = datetime_field(doc='Date and time the flag was resolved')
    updated_at: datetime = datetime_field(doc='Date and time the flag was last updated')
    user: property = LazyProperty(User.from_json, type=User, doc='User that added the flag')
    _populate_id_attrs = ['user_id']

    # Unused attributes
    # created_at_utc: datetime = datetime_field(doc='Date and time the flag was created (UTC)')
    # updated_at_utc: datetime = datetime_field(doc='Date and time the flag was last updated (UTC)')
    # user_id: int = field(default=None, doc='ID of the user who created the flag')

    @property
    def username(self) -> str:
        return self.user.login

    @property
    def _str_attrs(self) -> list[str]:
        return ['id', 'flag', 'resolved', 'username']


@define_model
class QualityMetric(BaseModel):
    """:fa:`list-check` An observation quality metric added by a user to an observation"""

    agree: bool = field(default=None, doc='Indicates if the user agrees with this metric')
    metric: str = field(default=None, doc='Quality metric name')
    user: property = LazyProperty(User.from_json, type=User, doc='User that added the metric')
    _populate_id_attrs = ['user_id']

    # Unused attributes
    # user_id: int = field(default=None, doc='ID of the user who added the metric')

    @property
    def username(self) -> str:
        return self.user.login

    @property
    def _row(self) -> TableRow:
        return {
            'ID': self.id,
            'Metric': self.metric,
            'Agree': self.agree,
            'User': self.user.login,
        }

    @property
    def _str_attrs(self) -> list[str]:
        return ['id', 'metric', 'agree', 'username']


@define_model
class Vote(BaseModel):
    """:fa:`check` A vote on a data quality assessment metric"""

    created_at: datetime = datetime_field(doc='Date and time the vote was created')
    user: property = LazyProperty(User.from_json, type=User, doc='User that added the vote')
    vote_flag: bool = field(default=None)
    vote_scope: str = field(default=None)
    _populate_id_attrs = ['user_id']

    # Unused attributes
    # user_id: int = field(default=None, doc='ID of the user who voted')

    @property
    def username(self) -> str:
        return self.user.login

    @property
    def _row(self) -> TableRow:
        return {
            'ID': self.id,
            'Flag': self.vote_flag,
            'User': self.user.login,
        }

    @property
    def _str_attrs(self) -> list[str]:
        return ['id', 'vote_flag', 'username']


# Uses the same schema as votes
@define_model
class Fave(Vote):
    """:fa:`star` An observation favorited by a user"""


@define_model_custom_init
class Observation(BaseModel):
    """:fa:`binoculars` An observation, based the schema of
    :v1:`GET /observations <Observations/get_observations>`
    """

    created_at: datetime = datetime_now_field(doc='Date and time the observation was created')
    captive: bool = field(
        default=None, doc='Indicates if the organism is non-wild (captive or cultivated)'
    )
    community_taxon_id: int = field(default=None, doc='The current community identification taxon')
    context_geoprivacy: str = field(default=None)
    context_taxon_geoprivacy: str = field(default=None)
    context_user_geoprivacy: str = field(default=None)
    description: str = field(default=None, doc='Observation description')
    geoprivacy: str = field(default=None, options=GEOPRIVACY_LEVELS, doc='Location privacy level')
    identifications_count: int = field(default=0, doc='Total number of identifications')
    identifications_most_agree: bool = field(
        default=None, doc='Indicates if most identifications agree with the community ID'
    )
    identifications_most_disagree: bool = field(
        default=None, doc='Indicates if most identifications disagree with the community ID'
    )
    identifications_some_agree: bool = field(
        default=None, doc='Indicates if some identifications agree with the community ID'
    )
    license_code: str = field(
        default=None, converter=upper, options=ALL_LICENSES, doc='Creative Commons license code'
    )
    location: Coordinates = coordinate_pair()
    mappable: bool = field(default=None, doc='Indicates if the observation can be shown on a map')
    num_identification_agreements: int = field(
        default=None, doc='Total identifications that agree with the community ID'
    )
    num_identification_disagreements: int = field(
        default=None, doc='Total identifications that disagree with the community ID'
    )
    oauth_application_id: str = field(
        default=None, doc='ID of the OAuth application used to create the observation, if any'
    )
    obscured: bool = field(
        default=None,
        doc='Indicates if coordinates are obscured (showing a broad approximate location on the map)',
    )
    observed_on: DateTime = datetime_field(doc='Date and time the organism was observed')
    outlinks: list[dict] = field(
        factory=list, doc='Linked observation pages on other sites (e.g., GBIF)'
    )
    out_of_range: bool = field(
        default=None, doc='Indicates if the taxon is observed outside of its known range'
    )
    owners_identification_from_vision: bool = field(
        default=None, doc="Indicates if the owner's ID was selected from computer vision results"
    )
    place_guess: str = field(default=None, doc='Place name determined from observation coordinates')
    place_ids: list[int] = field(
        factory=list, doc='Place IDs associated with the observation coordinates'
    )
    positional_accuracy: int = field(
        default=None, doc='GPS accuracy in meters (real accuracy, if obscured)'
    )
    preferences: dict[str, Any] = field(
        factory=dict,
        doc='Any user observation preferences (related to community IDs, coordinate access, etc.)',
    )
    private_location: Coordinates = coordinate_pair(
        doc=':fa:`lock` Private location in ``(latitude, longitude)`` decimal degrees'
    )
    private_place_ids: list[int] = field(
        factory=list, doc=':fa:`lock` Place IDs associated with the private observation coordinates'
    )
    private_place_guess: str = field(
        default=None, doc=':fa:`lock` Place name determined from private observation coordinates'
    )
    project_ids: list[int] = field(factory=list, doc='All associated project IDs')
    project_ids_with_curator_id: list[int] = field(
        factory=list, doc='Project IDs with a curator identification for this observation'
    )
    project_ids_without_curator_id: list[int] = field(
        factory=list, doc='Project IDs without curator identification for this observation'
    )
    public_positional_accuracy: int = field(
        default=None, doc='GPS accuracy in meters (not accurate if obscured)'
    )
    quality_grade: str = field(default=None, options=QUALITY_GRADES, doc='Quality grade')
    reviewed_by: list[int] = field(
        factory=list, doc='IDs of users who have reviewed the observation'
    )
    site_id: int = field(
        default=None, doc='Site ID for iNaturalist network members, or ``1`` for inaturalist.org'
    )
    species_guess: str = field(
        default=None, doc="Taxon name from observer's initial identification"
    )
    tags: list[str] = field(factory=list, doc='Arbitrary user tags added to the observation')
    taxon_geoprivacy: str = field(default=None)
    updated_at: DateTime = datetime_field(doc='Date and time the observation was last updated')
    uri: str = field(default=None, doc='Link to observation details page')
    viewer_trusted_by_observer: bool = field(
        default=None, doc='Observer trusts the authenticated user with access to hidden coordinates'
    )

    # Lazy-loaded model objects
    annotations: property = LazyProperty(
        Annotation.from_json_list, type=list[Annotation], doc='Observation annotations'
    )
    application: property = LazyProperty(
        Application.from_json, type=Application, doc='Application that created the observation'
    )
    comments: property = LazyProperty(
        Comment.from_json_list, type=list[Comment], doc='Observation comments'
    )
    faves: property = LazyProperty(
        Fave.from_json_list, type=list[Fave], doc='Users who have favorited the observation'
    )
    flags: property = LazyProperty(Flag.from_json_list, type=list[Flag], doc='Observation flags')
    identifications: property = LazyProperty(
        Identification.from_json_list, type=list[Identification], doc='Observation identifications'
    )
    ofvs: property = LazyProperty(
        ObservationFieldValue.from_json_list,
        type=list[ObservationFieldValue],
        doc='Observation field values',
    )
    photos: property = LazyProperty(
        Photo.from_json_list, type=list[Photo], doc='Observation photos'
    )
    project_observations: property = LazyProperty(
        ProjectObservation.from_json_list,
        type=list[ProjectObservation],
        doc='Details on any projects that the observation has been added to',
    )
    quality_metrics: property = LazyProperty(
        QualityMetric.from_json_list,
        type=list[QualityMetric],
        doc='Data quality assessment metrics',
    )
    sounds: property = LazyProperty(
        Sound.from_json_list, type=list[Sound], doc='Observation sound files'
    )
    taxon: property = LazyProperty(Taxon.from_json, type=Taxon, doc='Observation taxon')
    user: property = LazyProperty(User.from_json, type=User, doc='Observer')
    votes: property = LazyProperty(
        Vote.from_json_list, type=list[Vote], doc='Votes on data quality assessment metrics'
    )

    # Additional attributes from API response that aren't needed; just left here for reference
    # cached_votes_total: int = field(default=None)
    # comments_count: int = field(default=None)
    # community_taxon: property = LazyProperty(Taxon.from_json, type=Taxon)
    # created_at_details: Dict = field(factory=dict)
    # created_time_zone: str = field(default=None)
    # faves_count: int = field(default=None)
    # geojson: Dict = field(factory=dict)
    # id_please: bool = field(default=None)
    # map_scale: int = field(default=None)
    # non_owner_ids: List = field(factory=list)
    # non_traditional_projects: property = LazyProperty(Project.from_json_list, type=List[Project])
    # observed_on_details: Dict = field(factory=dict)
    # observed_on_string: str = field(default=None)
    # observation_photos: List[Photo] = field(converter=Photo.from_dict_list, factory=list)
    # observed_time_zone: str = field(default=None)
    # private_geojson: Dict = field(factory=dict)
    # spam: bool = field(default=None)
    # time_observed_at: DateTime = datetime_attr
    # time_zone_offset: str = field(default=None)

    # Attributes that will only be used during init and then omitted
    temp_attrs = ['time_observed_at']

    def __init__(self, **kwargs):
        # Convert observation timestamps prior to __attrs_init__
        observed_on = kwargs.pop('time_observed_at', None)
        if observed_on and not isinstance(kwargs.get('observed_on'), datetime):
            kwargs['observed_on'] = observed_on

        # Set default URL based on observation ID
        if not kwargs.get('uri'):
            kwargs['uri'] = f'{INAT_BASE_URL}/observations/{kwargs.get("id", "")}'

        # Set identifications_count if missing
        if kwargs.get('identifications') and not kwargs.get('identifications_count'):
            kwargs['identifications_count'] = len(kwargs['identifications'])

        # Add ancestor info to Observation.taxon based on identification data, if available
        if kwargs.get('taxon') and (idents := kwargs.get('identifications')):
            try:
                taxa_by_id = {
                    t['id']: t
                    for t in chain.from_iterable(
                        [i.get('taxon', {}).get('ancestors', []) for i in idents]
                    )
                }
                ancestors = [taxa_by_id.get(i) for i in kwargs['taxon'].get('ancestor_ids')]
                kwargs['taxon']['ancestors'] = list(filter(None, ancestors))
            except AttributeError:
                pass

        self.__attrs_init__(**kwargs)

    @property
    def cumulative_ids(self) -> tuple[int, int]:
        """Calculate the cumulative community ID score (agreements/total), as shown on the observation UI

        Returns:
            ``(agreements, total)``
        """
        idents_count = 0
        idents_agree = 0
        ident_taxon_ids = self.ident_taxon_ids

        for ident in filter(lambda i: i.current, self.identifications):
            user_taxon_ids = ident.taxon.ancestor_ids + [ident.taxon.id]
            if self.community_taxon_id in user_taxon_ids:
                # Count towards total & agree:
                if ident.taxon.id in ident_taxon_ids:
                    idents_count += 1
                    idents_agree += 1
            else:
                # Maverick counts against:
                idents_count += 1

        return (idents_agree, idents_count)

    @property
    def default_photo(self) -> Photo:
        """Get the default observation photo if any; otherwise use taxon default photo or icon"""
        if self.photos:
            return self.photos[0]
        elif self.taxon:
            return self.taxon.icon
        else:
            return IconPhoto.from_iconic_taxon('unknown')

    @property
    def formatted_location(self) -> str:
        """Format the observation coordinates + geoprivacy, if available"""
        coords = self.private_location or self.location
        if not coords or len(coords) < 2:
            return 'N/A'
        geoprivacy = f' ({self.geoprivacy})' if self.geoprivacy else ''
        return f'({coords[0]:.4f}, {coords[1]:.4f}){geoprivacy}'

    @property
    def ident_taxon_ids(self) -> list[int]:
        """Get all taxon IDs (including ancestors) from identifications"""
        ident_taxa = [
            ident.taxon for ident in self.identifications if ident.taxon and ident.current
        ]
        ident_ids = chain.from_iterable([t.ancestor_ids + [t.id] for t in ident_taxa])
        return list(set(ident_ids))

    @property
    def username(self) -> str:
        return self.user.login

    @property
    def _row(self) -> TableRow:
        return {
            'ID': self.id,
            'Taxon ID': self.taxon.id if self.taxon else None,
            'Taxon': self.taxon.rich_full_name if self.taxon else None,
            'Observed on': self.observed_on,
            'User': self.user.login,
            'Location': self.place_guess or self.location,
        }

    @property
    def _str_attrs(self) -> list[str]:
        return ['id', 'taxon', 'observed_on', 'username', 'place_guess']


@define_model_collection
class Observations(BaseModelCollection):
    """:fa:`binoculars` A collection of observations"""

    data: list[Observation] = field(factory=list, converter=Observation.from_json_list)

    @property
    def identifiers(self) -> list[User]:
        """Get all unique identifiers"""
        unique_users = {i.user.id: i.user for obs in self.data for i in obs.identifications}
        return list(unique_users.values())

    @property
    def observers(self) -> list[User]:
        """Get all unique observers"""
        unique_users = {obs.user.id: obs.user for obs in self.data}
        return list(unique_users.values())

    @property
    def photos(self) -> list[Photo]:
        """Get default photo for each observation"""
        return [obs.default_photo for obs in self.data]

    @property
    def taxa(self) -> list[Taxon]:
        """Get all unique taxa"""
        unique_taxa = {obs.taxon.id: obs.taxon for obs in self.data}
        return list(unique_taxa.values())

    @property
    def _str_attrs(self) -> list[str]:
        return ['data']


HIST_BAR_WIDTH = 50


@define_model
class HistogramBin(BaseModel):
    """:fa:`chart-bar` A single bin in a histogram.

    The main purpose of this class is for terminal formatting with :py:func:`.pprint`.
    """

    label: DateOrInt = field(default=None, doc='Bin label; type depends on interval')
    count: int = field(default=0, doc='Number of observations in this bin')
    interval: str = field(default=None, doc=f'Histogram interval; one of: {HISTOGRAM_INTERVALS}')
    max_count: int = field(
        default=0, repr=False, doc='Max count across all bins; used for normalization'
    )

    @property
    def bar_width(self) -> int:
        """A normalized count as a bar width for terminal display"""
        normalized_count = 0.0 if self.max_count == 0 else self.count / self.max_count
        return math.ceil(normalized_count * HIST_BAR_WIDTH)

    @property
    def interval_column_label(self) -> str:
        """Format the bin interval for display"""
        return self.interval.split('_')[0].capitalize() if self.interval else 'Value'

    @property
    def formatted_label(self) -> str:
        """Format the bin label for display, depending on the interval"""
        if self.interval == 'year' and isinstance(self.label, datetime):
            return self.label.strftime('%Y')
        elif self.interval == 'month' and isinstance(self.label, datetime):
            return self.label.strftime('%Y-%m')
        elif self.interval == 'week' and isinstance(self.label, datetime):
            return self.label.strftime('%Y-%m-%d')
        elif self.interval == 'month_of_year' and isinstance(self.label, int):
            return datetime(1999, self.label, 1).strftime('%b')
        else:
            return str(self.label)

    @property
    def _row(self) -> TableRow:
        return {
            self.interval_column_label: self.formatted_label,
            'Count': self.count,
            '': '█' * self.bar_width,
        }

    @property
    def _str_attrs(self) -> list[str]:
        return ['label', 'count']


@define_model_collection
class Histogram(BaseModelCollection):
    """:fa:`chart-bar` A histogram of observation counts.

    Use with :py:func:`.pprint` for formatted output, or get as a ``{bin: count}`` dict via ``.raw``.
    """

    data: list[HistogramBin] = field(factory=list, converter=HistogramBin.from_json_list)

    @classmethod
    def from_json(cls, value: JsonResponse, **kwargs) -> 'Histogram':
        hist_dict = convert_histogram(value)
        interval = get_histogram_interval(value)
        max_count = max(hist_dict.values()) if hist_dict else 0
        bins = [
            {'label': k, 'count': v, 'interval': interval, 'max_count': max_count}
            for k, v in hist_dict.items()
        ]
        return cls(data=bins)  # type: ignore [call-arg]

    @property
    def raw(self) -> HistogramResponse:
        """Histogram data as a simple dict of ``{bin: count}``"""
        return {b.label: b.count for b in self.data}

    @property
    def _str_attrs(self) -> list[str]:
        return ['data']


# Fix __init__ and class docstring
Observation = extend_init_signature(Observation.__attrs_init__)(Observation)  # type: ignore
