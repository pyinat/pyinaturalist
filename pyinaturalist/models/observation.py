# TODO
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

import attr

from pyinaturalist.constants import Coordinates
from pyinaturalist.models import (
    BaseModel,
    Identification,
    Identifications,
    ModelCollection,
    Photo,
    Photos,
    Taxa,
    Taxon,
    User,
    created_timestamp,
    kwarg,
    timestamp,
)
from pyinaturalist.node_api import get_observation
from pyinaturalist.response_format import convert_lat_long_str

# TODO
# coordinate_pair = attr.ib(converter=convert_lat_long_str, default=None)


@attr.s
class Observation(BaseModel):
    """A data class containing information about an observation, matching the schema of
    ``GET /observations`` from the iNaturalist API:
    https://api.inaturalist.org/v1/docs/#!/Observations/get_observations

    Can be constructed from either a full JSON record, a partial JSON record, or just an ID.
    """

    created_at: datetime = created_timestamp
    cached_votes_total: int = kwarg
    captive: bool = kwarg
    comments_count: int = kwarg
    community_taxon_id: int = kwarg
    description: str = kwarg
    faves_count: int = kwarg
    geoprivacy: str = kwarg  # Enum
    id: int = kwarg
    id_please: bool = kwarg
    identifications_count: int = kwarg
    identifications_most_agree: bool = kwarg
    identifications_most_disagree: bool = kwarg
    identifications_some_agree: bool = kwarg
    license_code: str = kwarg  # Enum
    location: Coordinates = attr.ib(converter=convert_lat_long_str, default=None)
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
    spam: bool = kwarg
    species_guess: str = kwarg
    time_observed_at: Optional[datetime] = timestamp
    updated_at: Optional[datetime] = timestamp
    uri: str = kwarg
    uuid: UUID = attr.ib(converter=UUID, default=None)

    # Nested collections with defaults
    annotations: List = attr.ib(factory=list)
    comments: List = attr.ib(factory=list)  # TODO: make separate model + condensed format
    faves: List = attr.ib(factory=list)
    flags: List = attr.ib(factory=list)
    identifications: ModelCollection[Identification] = attr.ib(
        converter=Identifications.from_json, factory=list
    )
    ofvs: List = attr.ib(factory=list)
    outlinks: List = attr.ib(factory=list)
    photos: ModelCollection[Photo] = attr.ib(converter=Photos.from_json, factory=list)
    place_ids: List = attr.ib(factory=list)
    preferences: Dict = attr.ib(factory=dict)
    project_ids: List = attr.ib(factory=list)
    project_ids_with_curator_id: List = attr.ib(factory=list)
    project_ids_without_curator_id: List = attr.ib(factory=list)
    project_observations: List = attr.ib(factory=list)
    quality_metrics: List = attr.ib(factory=list)
    reviewed_by: List = attr.ib(factory=list)
    sounds: List = attr.ib(factory=list)
    tags: List = attr.ib(factory=list)
    taxon: Taxon = attr.ib(converter=Taxon.from_json, default=None)
    user: User = attr.ib(converter=User.from_json, default=None)
    votes: List = attr.ib(factory=list)

    # Additional response fields that are redundant here; just left here for reference
    # created_at_details: Dict = attr.ib(factory=dict)
    # created_time_zone: str = kwarg
    # geojson: Dict = attr.ib(factory=dict)
    # non_owner_ids: List = attr.ib(factory=list)
    # observation_photos: List[Photo] = attr.ib(converter=Photo.from_dict_list, factory=list)
    # observed_on: date = timestamp
    # observed_on_details: Dict = attr.ib(factory=dict)
    # observed_on_string: datetime = timestamp
    # observed_time_zone: str = kwarg
    # time_zone_offset: "+01:00"

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

    # TODO: Return simplified dict
    # def simplify(self) -> Dict:
    #     pass

    # TODO
    # def __str__(self) -> str:
    #     pass


class Observations(ModelCollection):
    """A collection of observation records with some extra aggregate info"""

    model_cls = Observation

    # @classmethod
    # def from_csv(cls, path):
    #     """Load from a CSV export"""
    #     pass

    @property
    def identifiers(self) -> List[User]:
        """Get all unique identifiers"""
        unique_users = {
            ident.user.id: ident.user for obs in self.data for ident in obs.identifications
        }
        return list(unique_users.values())

    @property
    def taxa(self) -> Taxa:
        """Get all unique taxa"""
        unique_taxa = {obs.taxon.id: obs.taxon for obs in self.data}
        return Taxa(unique_taxa.values())

    @property
    def thumbnail_urls(self) -> List[str]:
        """Get thumbnails for all observation default photos"""
        return [obs.thumbnail_url for obs in self.data if obs.thumbnail_url]

    @property
    def users(self) -> List[User]:
        """Get all unique observers"""
        unique_users = {obs.user.id: obs.user for obs in self.data}
        return list(unique_users.values())

    # def to_dataframe(self):
    #     pass

    # def to_csv(self, filename=None):
    #     pass
