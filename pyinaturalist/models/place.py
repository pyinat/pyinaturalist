from typing import Dict, List, Union

from attr import field

from pyinaturalist.constants import INAT_BASE_URL, Coordinates, GeoJson, ResponseOrFile
from pyinaturalist.converters import convert_lat_long
from pyinaturalist.models import BaseModel, define_model, kwarg, load_json


def convert_optional_lat_long(obj: Union[Dict, List, None, str]):
    return convert_lat_long(obj) or (0, 0)


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
    location: Coordinates = field(converter=convert_optional_lat_long, default=None)
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

    @property
    def centroid(self) -> str:
        """Formatted centroid coordinates"""
        return f'({self.location[0]:.5f}, {self.location[1]:.5f})'

    @property
    def url(self) -> str:
        """Info URL on iNaturalist.org"""
        return f'{INAT_BASE_URL}/places/{self.id}'

    # Column headers for simplified table format
    headers = {
        'ID': 'cyan',
        'Name': 'green',
        'Centroid': 'blue',
        'Category': 'magenta',
        'URL': 'white',
    }

    @property
    def row(self) -> List:
        """Get basic values to display as a row in a table"""
        return [self.id, self.name, self.centroid, self.category or '', self.url]

    def __str__(self) -> str:
        return f'[{self.id}] {self.name}'
