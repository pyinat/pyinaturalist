from typing import Dict, List, Union

from attr import field

from pyinaturalist.constants import (
    INAT_BASE_URL,
    Coordinates,
    GeoJson,
    JsonResponse,
    ResponseOrResults,
    TableRow,
)
from pyinaturalist.converters import convert_lat_long
from pyinaturalist.models import BaseModel, define_model, kwarg
from pyinaturalist.models.base import ensure_list


def convert_optional_lat_long(obj: Union[Dict, List, None, str]):
    return convert_lat_long(obj) or (0, 0)


@define_model
class Place(BaseModel):
    """A curated or community-contributed place. Handles data from the following endpoints:

    * `GET /places/{id} <https://api.inaturalist.org/v1/docs/#!/Places/get_places_id>`_
    * `GET /places/nearby <https://api.inaturalist.org/v1/docs/#!/Places/get_places_nearby>`_
    * `GET /taxa <https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa>`_  (``establishment_means.place``)
    """

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
    def from_json(cls, value: JsonResponse, category: str = None, **kwargs) -> BaseModel:
        value.setdefault('category', category)
        return super(Place, cls).from_json(value)

    @classmethod
    def from_json_list(cls, value: ResponseOrResults, **kwargs) -> List[BaseModel]:
        """Optionally use results from /places/nearby to set Place.category"""
        json_value = dict(ensure_list(value)[0])
        if 'results' in json_value:
            json_value = json_value['results']

        if 'standard' in json_value and 'community' in json_value:
            places = [cls.from_json(item, category='standard') for item in json_value['standard']]
            places += [cls.from_json(item, category='community') for item in json_value['community']]
            return places
        else:
            return super(Place, cls).from_json_list(json_value)

    @property
    def ancestry(self) -> str:
        """Handle slash-delimited 'ancestry' string from ``establishment_means.place``"""
        return '/'.join(self.ancestor_place_ids)

    @ancestry.setter
    def ancestry(self, value: str):
        self.ancestor_place_ids = value.split('/')

    @property
    def url(self) -> str:
        """Info URL on iNaturalist.org"""
        return f'{INAT_BASE_URL}/places/{self.id}'

    @property
    def row(self) -> TableRow:
        return {
            'ID': self.id,
            'Latitude': f'{self.location[0]:9.4f}',
            'Longitude': f'{self.location[1]:9.4f}',
            'Name': self.name,
            'Category': self.category,
            'URL': self.url,
        }

    def __str__(self) -> str:
        return f'[{self.id}] {self.name}'
