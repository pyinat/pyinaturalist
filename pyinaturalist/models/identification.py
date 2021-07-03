from datetime import datetime

from pyinaturalist.constants import TableRow
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
    """An observation identification, based on the schema of
    `GET /identifications <https://api.inaturalist.org/v1/docs/#!/Identifications/get_identifications>`_.
    """

    body: str = field(default=None)
    category: str = field(default=None)  # Enum
    created_at: datetime = datetime_now_field(doc='Date and time the identification was added')
    current: bool = field(default=None)
    current_taxon: bool = field(default=None)
    disagreement: bool = field(default=None)
    hidden: bool = field(default=None)
    own_observation: bool = field(default=None)
    previous_observation_taxon_id: int = field(default=None)
    taxon_change: bool = field(default=None)  # TODO: confirm type
    taxon_id: int = field(default=None)
    uuid: str = field(default=None)
    vision: bool = field(default=None)

    # Lazy-loaded nested model objects
    taxon: property = LazyProperty(Taxon.from_json)
    user: property = LazyProperty(User.from_json)

    # Unused attributes
    # created_at_details: {}
    # spam: bool = field(default=None)
    # flags: List = field(factory=list)
    # moderator_actions: List = field(factory=list)
    # observation: {}

    @property
    def row(self) -> TableRow:
        return {
            'ID': self.id,
            'Taxon ID': self.taxon.id,
            'Taxon': self.taxon.full_name,
            'User': self.user.login,
            'Category': self.category.title(),
            'From CV': self.vision,
        }

    def __str__(self) -> str:
        """Format into a condensed summary: id, what, when, and who"""
        return (
            f'[{self.id}] {self.taxon.full_name} ({self.category}) added on {self.created_at} '
            f'by {self.user.login}'
        )
