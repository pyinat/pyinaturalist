from datetime import datetime
from typing import Dict, List, Optional

from attr import define, field

from pyinaturalist.constants import Coordinates, TableRow
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
    kwarg,
)
from pyinaturalist.v1 import get_observation


@define(auto_attribs=False, init=False, field_transformer=add_lazy_attrs)
class Observation(BaseModel):
    """An observation, based the schema of
    `GET /observations <https://api.inaturalist.org/v1/docs/#!/Observations/get_observations>`_.
    """

    created_at: datetime = datetime_now_attr
    cached_votes_total: int = kwarg
    captive: bool = kwarg
    comments_count: int = kwarg
    community_taxon_id: int = kwarg
    description: str = kwarg
    faves_count: int = kwarg
    geoprivacy: str = kwarg  # Enum
    id_please: bool = kwarg
    identifications_count: int = kwarg
    identifications_most_agree: bool = kwarg
    identifications_most_disagree: bool = kwarg
    identifications_some_agree: bool = kwarg
    license_code: str = kwarg  # Enum
    location: Optional[Coordinates] = coordinate_pair
    map_scale: int = kwarg
    mappable: bool = kwarg
    num_identification_agreements: int = kwarg
    num_identification_disagreements: int = kwarg
    oauth_application_id: str = kwarg
    obscured: bool = kwarg
    out_of_range: bool = kwarg
    owners_identification_from_vision: bool = kwarg
    place_guess: str = kwarg
    positional_accuracy: int = kwarg
    public_positional_accuracy: int = kwarg
    quality_grade: str = kwarg  # Enum
    site_id: int = kwarg
    species_guess: str = kwarg
    observed_on: Optional[datetime] = datetime_attr
    updated_at: Optional[datetime] = datetime_attr
    uri: str = kwarg
    uuid: str = kwarg

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
    # created_at_details: Dict = field(factory=dict)
    # created_time_zone: str = kwarg
    # flags: List = field(factory=list)
    # geojson: Dict = field(factory=dict)
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
