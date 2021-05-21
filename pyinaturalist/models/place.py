from typing import Dict, List, Optional

from attr import define, field

from pyinaturalist.constants import Coordinates
from pyinaturalist.models import BaseModel, coordinate_pair, kwarg

# TODO: Make a separate model for geojson type? or optionally use `geojson` library?
GeoJson = Dict


@define(auto_attribs=False)
class Place(BaseModel):
    admin_level: int = kwarg
    ancestor_place_ids: List[str] = field(factory=list)
    bbox_area: float = kwarg
    bounding_box_geojson: GeoJson = field(factory=dict)
    category: str = kwarg  # Either 'standard' or 'community'
    display_name: str = kwarg
    geometry_geojson: GeoJson = field(factory=dict)
    id: int = kwarg
    location: Optional[Coordinates] = coordinate_pair
    name: str = kwarg
    place_type: int = kwarg
    slug: str = kwarg

    # TODO: Use results from /places/nearby to set Place.category
    # @classmethod
    # def from_json_list(cls, value):
    #     pass
