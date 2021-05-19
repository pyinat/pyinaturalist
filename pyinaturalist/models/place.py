from typing import Dict, List, Optional

import attr

from pyinaturalist.constants import Coordinates
from pyinaturalist.models import BaseModel, coordinate_pair, kwarg

# TODO: Make a separate model for geojson type? or optionally use `geojson` library?
GeoJson = Dict


@attr.s
class Place(BaseModel):
    admin_level: int = kwarg
    ancestor_place_ids: List[str] = attr.ib(factory=list)
    bbox_area: float = kwarg
    bounding_box_geojson: GeoJson = attr.ib(factory=dict)
    category: str = kwarg  # Either 'standard' or 'community'
    display_name: str = kwarg
    geometry_geojson: GeoJson = attr.ib(factory=dict)
    id: int = kwarg
    location: Optional[Coordinates] = coordinate_pair
    name: str = kwarg
    place_type: int = kwarg
    slug: str = kwarg
