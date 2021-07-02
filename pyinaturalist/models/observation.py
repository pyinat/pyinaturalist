from datetime import datetime
from typing import Dict, List, Optional

from attr import define, field

from pyinaturalist.constants import CC_LICENSES, GEOPRIVACY_LEVELS, Coordinates, QUALITY_GRADES, TableRow
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
    datetime_attr,
    datetime_now_attr,
    define_model_collection,
    is_in,
    kwarg,
)
from pyinaturalist.v1 import get_observation


def upper(value) -> Optional[str]:
    return str(value).upper() if value is not None else None


@define(auto_attribs=False, init=False, field_transformer=add_lazy_attrs)
class Observation(BaseModel):
    """An observation, based the schema of
    `GET /observations <https://api.inaturalist.org/v1/docs/#!/Observations/get_observations>`_.
    """

    created_at: datetime = datetime_now_attr  #: Date and time this was created
    captive: bool = kwarg  #: Indicates if the organism is non-wild (captive or cultivated)
    community_taxon_id: int = kwarg  #: The current community identification taxon
    description: str = kwarg  #: Observation description
    #: Location privacy level: either 'open', 'obscured', or 'private
    geoprivacy: str = field(default=None, validator=is_in(GEOPRIVACY_LEVELS))
    identifications_count: int = kwarg  #: Total number of identifications
    identifications_most_agree: bool = kwarg  #: Indicates if most identifications agree
    identifications_most_disagree: bool = kwarg  #: Indicates if most identifications disagree
    identifications_some_agree: bool = kwarg  #: Indicates if some identifications agree
    #: Creative Commons license code
    license_code: str = field(default=None, converter=upper, validator=is_in(CC_LICENSES))
    location: Optional[Coordinates] = coordinate_pair  #: Latitude and logitude in decimal degrees
    mappable: bool = kwarg  #: Indicates if the observation can be shown on a map
    num_identification_agreements: int = kwarg  #: Total number of agreeing identifications
    num_identification_disagreements: int = kwarg  #: Total number of disagreeing identifications
    oauth_application_id: str = kwarg  #: OAuth application ID used to create the observation, if any
    obscured: bool = kwarg  #: Indicates if coordinates are obscured
    out_of_range: bool = kwarg  #: Indicates if the taxon is observed outside of its known range
    #: Indicates if the owner's ID was selected from computer visino results
    owners_identification_from_vision: bool = kwarg
    place_guess: str = kwarg  #: Place name determined from observation coordinates
    positional_accuracy: int = kwarg  #: GPS accuracy in meters (real accuracy, if obscured)
    public_positional_accuracy: int = kwarg  #: GPS accuracy in meters (not accurate if obscured)
    quality_grade: str = field(default=None, validator=is_in(QUALITY_GRADES))  #: Quality grade
    site_id: int = kwarg  #: Site ID for iNaturalist network members, or 1 for inaturalist.org
    species_guess: str = kwarg  #: Species name from observer's initial identification
    observed_on: Optional[datetime] = datetime_attr  #: Date and time this was observed
    updated_at: Optional[datetime] = datetime_attr  #: Date and time this was last updated
    uri: str = kwarg  #: Link to observation details page
    uuid: str = kwarg  #: Universally unique ID; generally preferred over 'id' where possible

    # Nested collections
    faves: List = field(factory=list)
    outlinks: List = field(factory=list)
    place_ids: List = field(factory=list)
    preferences: Dict = field(factory=dict)
    project_ids: List = field(factory=list)
    project_ids_with_curator_id: List = field(factory=list)
    project_ids_without_curator_id: List = field(factory=list)
    quality_metrics: List = field(factory=list)
    reviewed_by: List = field(factory=list)
    sounds: List = field(factory=list)
    tags: List = field(factory=list)
    votes: List = field(factory=list)

    # Lazy-loaded nested model objects
    annotations: property = LazyProperty(Annotation.from_json_list)
    comments: property = LazyProperty(Comment.from_json_list)
    identifications: property = LazyProperty(Identification.from_json_list)
    ofvs: property = LazyProperty(ObservationFieldValue.from_json_list)
    photos: property = LazyProperty(Photo.from_json_list)
    project_observations: property = LazyProperty(ProjectObservation.from_json_list)
    taxon: property = LazyProperty(Taxon.from_json)
    user: property = LazyProperty(User.from_json)

    # Additional attributes from API response that aren't needed; just left here for reference
    # cached_votes_total: int = kwarg
    # comments_count: int = kwarg
    # created_at_details: Dict = field(factory=dict)
    # created_time_zone: str = kwarg
    # faves_count: int = kwarg
    # flags: List = field(factory=list)
    # geojson: Dict = field(factory=dict)
    # id_please: bool = kwarg
    # map_scale: int = kwarg
    # non_owner_ids: List = field(factory=list)
    # observed_on_details: Dict = field(factory=dict)
    # observed_on_string: str = kwarg
    # observation_photos: List[Photo] = field(converter=Photo.from_dict_list, factory=list)
    # observed_time_zone: str = kwarg
    # spam: bool = kwarg
    # time_observed_at: Optional[datetime] = datetime_attr
    # time_zone_offset: str = kwarg

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
    """A collection of observations"""

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
