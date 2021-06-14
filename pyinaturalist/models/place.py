from typing import Dict, List, Optional, Union

from attr import field

from pyinaturalist.constants import Coordinates, ResponseOrFile
from pyinaturalist.models import BaseModel, coordinate_pair, define_model, kwarg, load_json

# TODO: Optionally use `geojson` library for users who want to use place geojson?
GeoJson = Dict


@define_model
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

    @classmethod
    def from_json(cls, value: ResponseOrFile, category: str = None, **kwargs):
        json_value = load_json(value)
        json_value.setdefault('category', category)
        return super(Place, cls).from_json(json_value)

    @classmethod
    def from_json_list(cls, value: Union[ResponseOrFile, List[ResponseOrFile]], **kwargs):
        """Optionally use results from /places/nearby to set Place.category"""
        json_value = load_json(value)  # type: ignore

        if 'standard' in json_value and 'community' in json_value:
            places = [cls.from_json(item, category='standard') for item in json_value['standard']]
            places += [cls.from_json(item, category='community') for item in json_value['community']]
            return places
        else:
            return super(Place, cls).from_json_list(json_value)

    def __str__(self) -> str:
        return f'[{self.id}] {self.name}'
