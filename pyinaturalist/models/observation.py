# TODO: Possible models for faves, sounds, and votes?
from datetime import datetime
from typing import Any, Dict, List, Optional

from attr import define

from pyinaturalist.constants import (
    ALL_LICENSES,
    GEOPRIVACY_LEVELS,
    QUALITY_GRADES,
    Coordinates,
    DateTime,
    TableRow,
)
from pyinaturalist.converters import convert_observation_timestamp
from pyinaturalist.models import (
    Annotation,
    BaseModel,
    BaseModelCollection,
    Comment,
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
from pyinaturalist.v1 import get_observation


@define(auto_attribs=False, init=False, field_transformer=add_lazy_attrs)
class Observation(BaseModel):
    """:fa:`binoculars` An observation, based the schema of
    `GET /observations <https://api.inaturalist.org/v1/docs/#!/Observations/get_observations>`_.
    """

    created_at: datetime = datetime_now_field(doc='Date and time the observation was created')
    captive: bool = field(
        default=None, doc='Indicates if the organism is non-wild (captive or cultivated)'
    )
    community_taxon_id: int = field(default=None, doc='The current community identification taxon')
    description: str = field(default=None, doc='Observation description')
    faves: List[Dict] = field(factory=list, doc='Details on users who have favorited the observation')
    geoprivacy: str = field(default=None, options=GEOPRIVACY_LEVELS, doc='Location privacy level')
    identifications_count: int = field(default=None, doc='Total number of identifications')
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
    place_ids: List[int] = field(factory=list)
    positional_accuracy: int = field(
        default=None, doc='GPS accuracy in meters (real accuracy, if obscured)'
    )
    preferences: Dict[str, Any] = field(
        factory=dict,
        doc='Any user observation preferences (related to community IDs, coordinate access, etc.)',
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
    reviewed_by: List[int] = field(factory=list, doc='IDs of users who have reviewed the observation')
    site_id: int = field(
        default=None, doc='Site ID for iNaturalist network members, or ``1`` for inaturalist.org'
    )
    sounds: List[Dict] = field(factory=list, doc='Observation sound files')
    species_guess: str = field(default=None, doc="Taxon name from observer's initial identification")
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
    photos: property = LazyProperty(Photo.from_json_list, type=List[Photo], doc='Observation photos')
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
    temp_attrs = [
        'created_at_details',
        'observed_on_string',
        'observed_time_zone',
        'time_zone_offset',
    ]

    # Convert observation timestamps prior to attrs init
    # TODO: better function signature for docs; use forge?
    def __init__(
        self,
        created_at_details: Dict = None,
        observed_on_string: str = None,
        observed_time_zone: str = None,
        time_zone_offset: str = None,
        **kwargs,
    ):
        tz_offset = time_zone_offset
        tz_name = observed_time_zone
        created_date = (created_at_details or {}).get('date')

        if not isinstance(kwargs.get('created_at'), datetime) and created_date:
            kwargs['created_at'] = convert_observation_timestamp(created_date, tz_offset, tz_name)
        if not isinstance(kwargs.get('observed_on'), datetime) and observed_on_string:
            kwargs['observed_on'] = convert_observation_timestamp(
                observed_on_string, tz_offset, tz_name, ignoretz=True
            )

        self.__attrs_init__(**kwargs)  # type: ignore

    @classmethod
    def from_id(cls, id: int):
        """Lookup and create a new Observation object from an ID"""
        json = get_observation(id)
        return cls.from_json(json)

    @property
    def thumbnail_url(self) -> Optional[str]:
        """Thumbnail URL for first observation photo (if any)"""
        if not self.photos:
            return None
        return self.photos[0].thumbnail_url

    @property
    def row(self) -> TableRow:
        return {
            'ID': self.id,
            'Taxon ID': self.taxon.id,
            'Taxon': self.taxon.full_name,
            'Observed on': self.observed_on,
            'User': self.user.login,
            'Location': self.place_guess or self.location,
        }

    def __str__(self) -> str:
        return (
            f'[{self.id}] {self.taxon.full_name} '
            f'observed on {self.observed_on} by {self.user.login} '
            f'at {self.place_guess or self.location}'
        )


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
    def taxa(self) -> List[Taxon]:
        """Get all unique taxa"""
        unique_taxa = {obs.taxon.id: obs.taxon for obs in self.data}
        return list(unique_taxa.values())

    @property
    def thumbnail_urls(self) -> List[str]:
        """Get thumbnails for all observation default photos"""
        return [obs.thumbnail_url for obs in self.data if obs.thumbnail_url]
