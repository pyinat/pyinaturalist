from datetime import datetime
from typing import Any, Dict, List

from attr import define

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
    Taxon,
    User,
    add_lazy_attrs,
    coordinate_pair,
    datetime_field,
    datetime_now_field,
    define_model_collection,
    field,
    upper,
)


@define(auto_attribs=False, init=False, field_transformer=add_lazy_attrs)
class Observation(BaseModel):
    """:fa:`binoculars` An observation, based the schema of
    :v1:`GET /observations <Observations/get_observations>`
    """

    created_at: datetime = datetime_now_field(doc='Date and time the observation was created')
    captive: bool = field(
        default=None, doc='Indicates if the organism is non-wild (captive or cultivated)'
    )
    community_taxon_id: int = field(default=None, doc='The current community identification taxon')
    description: str = field(default=None, doc='Observation description')
    faves: List[Dict] = field(
        factory=list, doc='Details on users who have favorited the observation'
    )
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
    sounds: List[Dict] = field(factory=list, doc='Observation sound files')
    species_guess: str = field(
        default=None, doc="Taxon name from observer's initial identification"
    )
    tags: List[str] = field(factory=list, doc='Arbitrary user tags added to the observation')
    updated_at: DateTime = datetime_field(doc='Date and time the observation was last updated')
    uri: str = field(default=None, doc='Link to observation details page')
    uuid: str = field(
        default=None, doc='Universally unique ID; generally preferred over ``id`` where possible'
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
    taxon: property = LazyProperty(Taxon.from_json, type=Taxon, doc='Observation taxon')
    user: property = LazyProperty(User.from_json, type=User, doc='Observer')

    # Additional attributes from API response that aren't needed; just left here for reference
    # cached_votes_total: int = field(default=None)
    # comments_count: int = field(default=None)
    # created_at_details: Dict = field(factory=dict)
    # created_time_zone: str = field(default=None)
    # faves_count: int = field(default=None)
    # flags: List = field(factory=list)
    # geojson: Dict = field(factory=dict)
    # id_please: bool = field(default=None)
    # map_scale: int = field(default=None)
    # non_owner_ids: List = field(factory=list)
    # observed_on_details: Dict = field(factory=dict)
    # observed_on_string: str = field(default=None)
    # observation_photos: List[Photo] = field(converter=Photo.from_dict_list, factory=list)
    # observed_time_zone: str = field(default=None)
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
    def default_photo(self) -> Photo:
        """Get the default observation photo if any; otherwise use taxon default photo or icon"""
        if self.photos:
            return self.photos[0]
        elif self.taxon:
            return self.taxon.icon
        else:
            return IconPhoto.from_iconic_taxon('unknown')

    @property
    def _row(self) -> TableRow:
        return {
            'ID': self.id,
            'Taxon ID': self.taxon.id,
            'Taxon': self.taxon.full_name,
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
