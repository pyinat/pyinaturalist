from typing import Dict, List, Optional, Union

from pyinaturalist.constants import (
    INAT_BASE_URL,
    PLACE_CATEGORIES,
    Coordinates,
    GeoJson,
    JsonResponse,
    ResponseOrResults,
    TableRow,
)
from pyinaturalist.converters import convert_lat_long
from pyinaturalist.models import BaseModel, define_model, field, is_in
from pyinaturalist.models.base import ensure_list


def convert_optional_lat_long(obj: Union[Dict, List, None, str]):
    return convert_lat_long(obj) or (0, 0)


@define_model
class Place(BaseModel):
    """:fa:`location-dot` A curated or community-contributed place. Handles data from the following endpoints:

    * `GET /places/{id} <https://api.inaturalist.org/v1/docs/#!/Places/get_places_id>`_
    * `GET /places/nearby <https://api.inaturalist.org/v1/docs/#!/Places/get_places_nearby>`_
    * `GET /taxa <https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa>`_  (``establishment_means.place``)
    """

    admin_level: int = field(default=None, doc='Administrative level, if any')
    ancestor_place_ids: List[str] = field(
        factory=list, doc='IDs of places that this place is contained within'
    )
    bbox_area: float = field(default=None, doc='Bounding box area')
    bounding_box_geojson: GeoJson = field(
        factory=dict, doc='Bounding box polygon that fully encloses the place'
    )
    category: str = field(
        default=None,
        validator=is_in(PLACE_CATEGORIES),
        doc='Place category (only applies to /places/nearby)',
    )
    display_name: str = field(default=None, doc='Place name as displayed on place info page')
    geometry_geojson: GeoJson = field(factory=dict, doc='Polygon representing place boundary')
    location: Coordinates = field(
        default=None,
        converter=convert_optional_lat_long,
        doc='Location in ``(latitude, logitude)`` decimal degrees',
    )
    name: str = field(default=None, doc='Place name')
    place_type: int = field(default=None, doc='Place type ID')
    place_type_name: str = field(default=None, doc='Place type name')
    slug: str = field(default=None, doc='Place URL slug')

    @classmethod
    def from_json(cls, value: JsonResponse, category: Optional[str] = None, **kwargs) -> 'Place':
        value.setdefault('category', category)
        return super(Place, cls).from_json(value)

    @classmethod
    def from_json_list(cls, value: ResponseOrResults, **kwargs) -> List['Place']:
        """Optionally use results from /places/nearby to set Place.category"""
        json_value = dict(ensure_list(value)[0])
        if 'results' in json_value:
            json_value = json_value['results']

        if 'standard' in json_value and 'community' in json_value:
            places = [cls.from_json(item, category='standard') for item in json_value['standard']]
            places += [
                cls.from_json(item, category='community') for item in json_value['community']
            ]
            return places
        else:
            return super(Place, cls).from_json_list(value)

    @property
    def ancestry(self) -> str:
        """Handle slash-delimited 'ancestry' string from ``establishment_means.place``"""
        return '/'.join(self.ancestor_place_ids)

    @ancestry.setter
    def ancestry(self, value: str):
        self.ancestor_place_ids = value.split('/')

    @property
    def url(self) -> str:
        """Place info URL on iNaturalist.org"""
        return f'{INAT_BASE_URL}/places/{self.id}'

    @property
    def _row(self) -> TableRow:
        return {
            'ID': self.id,
            'Latitude': f'{self.location[0]:9.4f}',
            'Longitude': f'{self.location[1]:9.4f}',
            'Name': self.name,
            'Category': self.category,
            'URL': self.url,
        }

    @property
    def _str_attrs(self) -> List[str]:
        return ['id', 'location', 'name']
