from datetime import datetime
from itertools import chain
from typing import Any, Dict, List, Tuple
from warnings import warn

from pyinaturalist.constants import (
    ALL_LICENSES,
    GEOPRIVACY_LEVELS,
    INAT_BASE_URL,
    QUALITY_GRADES,
    Coordinates,
    DateTime,
    TableRow,
)
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
    define_model_collection,
    define_model_custom_init,
    field,
    upper,
)


@define_model_custom_init
class Observation(BaseModel):
    """:fa:`binoculars` An observation, based the schema of
    :v1:`GET /observations <Observations/get_observations>`
    """

    application: Dict = field(factory=dict, doc='Application that created the observation')
    created_at: datetime = datetime_now_field(doc='Date and time the observation was created')
    captive: bool = field(
        default=None, doc='Indicates if the organism is non-wild (captive or cultivated)'
    )
    community_taxon_id: int = field(default=None, doc='The current community identification taxon')
    context_geoprivacy: str = field(default=None)
    context_taxon_geoprivacy: str = field(default=None)
    context_user_geoprivacy: str = field(default=None)
    description: str = field(default=None, doc='Observation description')
    faves: List[Dict] = field(
        factory=list, doc='Details on users who have favorited the observation'
    )
    flags: List[Dict] = field(factory=list)
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
    outlinks: List[Dict] = field(
        factory=list, doc='Linked observation pages on other sites (e.g., GBIF)'
    )
    out_of_range: bool = field(
        default=None, doc='Indicates if the taxon is observed outside of its known range'
    )
    owners_identification_from_vision: bool = field(
        default=None, doc="Indicates if the owner's ID was selected from computer vision results"
    )
    place_guess: str = field(default=None, doc='Place name determined from observation coordinates')
    place_ids: List[int] = field(
        factory=list, doc='Place IDs associated with the observation coordinates'
    )
    positional_accuracy: int = field(
        default=None, doc='GPS accuracy in meters (real accuracy, if obscured)'
    )
    preferences: Dict[str, Any] = field(
        factory=dict,
        doc='Any user observation preferences (related to community IDs, coordinate access, etc.)',
    )
    private_location: Coordinates = coordinate_pair(
        doc=':fa:`lock` Private location in ``(latitude, logitude)`` decimal degrees'
    )
    private_place_ids: List[int] = field(
        factory=list, doc=':fa:`lock` Place IDs associated with the private observation coordinates'
    )
    private_place_guess: str = field(
        default=None, doc=':fa:`lock` Place name determined from private observation coordinates'
    )
    project_ids: List[int] = field(factory=list, doc='All associated project IDs')
    project_ids_with_curator_id: List[int] = field(
        factory=list, doc='Project IDs with a curator identification for this observation'
    )
    project_ids_without_curator_id: List[int] = field(
        factory=list, doc='Project IDs without curator identification for this observation'
    )
    public_positional_accuracy: int = field(
        default=None, doc='GPS accuracy in meters (not accurate if obscured)'
    )
    quality_grade: str = field(default=None, options=QUALITY_GRADES, doc='Quality grade')
    quality_metrics: List[Dict] = field(factory=list, doc='Data quality assessment metrics')
    reviewed_by: List[int] = field(
        factory=list, doc='IDs of users who have reviewed the observation'
    )
    site_id: int = field(
        default=None, doc='Site ID for iNaturalist network members, or ``1`` for inaturalist.org'
    )
    species_guess: str = field(
        default=None, doc="Taxon name from observer's initial identification"
    )
    tags: List[str] = field(factory=list, doc='Arbitrary user tags added to the observation')
    taxon_geoprivacy: str = field(default=None)
    updated_at: DateTime = datetime_field(doc='Date and time the observation was last updated')
    uri: str = field(default=None, doc='Link to observation details page')
    uuid: str = field(
        default=None, doc='Universally unique ID; generally preferred over ``id`` where possible'
    )
    viewer_trusted_by_observer: bool = field(
        default=None, doc='Observer trusts the authenticated user with access to hidden coordinates'
    )
    votes: List[Dict] = field(factory=list, doc='Votes on data quality assessment metrics')

    # Lazy-loaded model objects
    annotations: property = LazyProperty(
        Annotation.from_json_list, type=List[Annotation], doc='Observation annotations'
    )
    comments: property = LazyProperty(
        Comment.from_json_list, type=List[Comment], doc='Observation comments'
    )
    identifications: property = LazyProperty(
        Identification.from_json_list, type=List[Identification], doc='Observation identifications'
    )
    ofvs: property = LazyProperty(
        ObservationFieldValue.from_json_list,
        type=List[ObservationFieldValue],
        doc='Observation field values',
    )
    photos: property = LazyProperty(
        Photo.from_json_list, type=List[Photo], doc='Observation photos'
    )
    project_observations: property = LazyProperty(
        ProjectObservation.from_json_list,
        type=List[ProjectObservation],
        doc='Details on any projects that the observation has been added to',
    )
    sounds: property = LazyProperty(
        Sound.from_json_list, type=List[Sound], doc='Observation sound files'
    )
    taxon: property = LazyProperty(Taxon.from_json, type=Taxon, doc='Observation taxon')
    user: property = LazyProperty(User.from_json, type=User, doc='Observer')

    # Additional attributes from API response that aren't needed; just left here for reference
    # cached_votes_total: int = field(default=None)
    # comments_count: int = field(default=None)
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
        if not isinstance(kwargs['observed_on'], datetime) and observed_on:
            kwargs['observed_on'] = observed_on
        # Set default URL based on observation ID
        if not kwargs.get('uri'):
            kwargs['uri'] = f'{INAT_BASE_URL}/observations/{kwargs.get("id", "")}'
        # Set identifications_count if missing
        if kwargs.get('identifications') and not kwargs.get('identifications_count'):
            kwargs['identifications_count'] = len(kwargs['identifications'])
        self.__attrs_init__(**kwargs)  # type: ignore

    @classmethod
    def from_id(cls, id: int):
        """Lookup and create a new Observation object from an ID"""
        from pyinaturalist.v1 import get_observation

        json = get_observation(id)
        return cls.from_json(json)

    @property
    def cumulative_ids(self) -> Tuple[int, int]:
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
    def ident_taxon_ids(self) -> List[int]:
        """Get all taxon IDs (including ancestors) from identifications"""
        ident_taxa = [ident.taxon for ident in self.identifications if ident.taxon]
        ident_ids = chain.from_iterable([t.ancestor_ids + [t.id] for t in ident_taxa])
        return list(set(ident_ids))

    @property
    def _row(self) -> TableRow:
        return {
            'ID': self.id,
            'Taxon ID': self.taxon.id if self.taxon else None,
            'Taxon': self.taxon.full_name if self.taxon else None,
            'Observed on': self.observed_on,
            'User': self.user.login,
            'Location': self.place_guess or self.location,
        }

    @property
    def _str_attrs(self) -> List[str]:
        return ['id', 'taxon', 'observed_on', 'user', 'place_guess']


@define_model_collection
class Observations(BaseModelCollection):
    """:fa:`binoculars` A collection of observations"""

    data: List[Observation] = field(factory=list, converter=Observation.from_json_list)

    @property
    def identifiers(self) -> List[User]:
        """Get all unique identifiers"""
        unique_users = {i.user.id: i.user for obs in self.data for i in obs.identifications}
        return list(unique_users.values())

    @property
    def observers(self) -> List[User]:
        """Get all unique observers"""
        unique_users = {obs.user.id: obs.user for obs in self.data}
        return list(unique_users.values())

    @property
    def photos(self) -> List[Photo]:
        """Get default photo for each observation"""
        return [obs.default_photo for obs in self.data]

    @property
    def taxa(self) -> List[Taxon]:
        """Get all unique taxa"""
        unique_taxa = {obs.taxon.id: obs.taxon for obs in self.data}
        return list(unique_taxa.values())


# Fix __init__ and class docstring
Observation = extend_init_signature(Observation.__attrs_init__)(Observation)  # type: ignore
