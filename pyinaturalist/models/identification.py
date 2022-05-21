from datetime import datetime
from typing import List

from pyinaturalist.constants import ID_CATEGORIES, TableRow
from pyinaturalist.models import (
    BaseModel,
    LazyProperty,
    Taxon,
    User,
    datetime_now_field,
    define_model,
    field,
)


@define_model
class Identification(BaseModel):
    """:fa:`fingerprint,style=fas` An observation identification, based on the schema of
    `GET /identifications <https://api.inaturalist.org/v1/docs/#!/Identifications/get_identifications>`_.
    """

    body: str = field(default=None, doc='Comment text')
    category: str = field(default=None, options=ID_CATEGORIES, doc='Identification category')
    created_at: datetime = datetime_now_field(doc='Date and time the identification was added')
    current: bool = field(
        default=None, doc='Indicates if the identification is the currently accepted one'
    )
    current_taxon: bool = field(default=None)
    disagreement: bool = field(
        default=None, doc='Indicates if this identification disagrees with previous ones'
    )
    hidden: bool = field(default=None)
    own_observation: bool = field(
        default=None, doc='Indicates if the indentifier is also the observer'
    )
    previous_observation_taxon_id: int = field(default=None, doc='Previous observation taxon ID')
    taxon_change: bool = field(default=None)  # TODO: confirm type
    taxon_id: int = field(default=None, doc='Identification taxon ID')
    uuid: str = field(default=None, doc='Universally unique identifier')
    vision: bool = field(
        default=None, doc='Indicates if the taxon was selected from computer vision results'
    )
    taxon: property = LazyProperty(Taxon.from_json, type=Taxon, doc='Identification taxon')
    user: property = LazyProperty(
        User.from_json, type=User, doc='User that added the indentification'
    )

    @property
    def taxon_name(self) -> str:
        return self.taxon.full_name

    # Unused attributes
    # created_at_details: {}
    # spam: bool = field(default=None)
    # flags: List = field(factory=list)
    # moderator_actions: List = field(factory=list)
    # observation: {}

    @property
    def _row(self) -> TableRow:
        return {
            'ID': self.id,
            'Taxon ID': self.taxon.id,
            'Taxon': f'{self.taxon.emoji} {self.taxon.full_name}',
            'User': self.user.login,
            'Category': self.category.title(),
            'From CV': self.vision,
        }

    @property
    def _str_attrs(self) -> List[str]:
        return ['id', 'taxon_name', 'created_at']
