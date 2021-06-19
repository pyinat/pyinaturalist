from datetime import datetime

from pyinaturalist.constants import TableRow
from pyinaturalist.models import (
    BaseModel,
    LazyProperty,
    Taxon,
    User,
    datetime_now_attr,
    define_model,
    kwarg,
)


@define_model
class Identification(BaseModel):
    """A dataclass containing information about an identification, matching the schema of
    `GET /identifications <https://api.inaturalist.org/v1/docs/#!/Identifications/get_identifications>`_.
    """

    body: str = kwarg
    category: str = kwarg  # Enum
    created_at: datetime = datetime_now_attr
    current: bool = kwarg
    current_taxon: bool = kwarg
    disagreement: bool = kwarg
    hidden: bool = kwarg
    id: int = kwarg
    own_observation: bool = kwarg
    previous_observation_taxon_id: int = kwarg
    taxon_change: bool = kwarg  # TODO: confirm type
    taxon_id: int = kwarg
    uuid: str = kwarg
    vision: bool = kwarg

    # Lazy-loaded nested model objects
    taxon: property = LazyProperty(Taxon.from_json)
    user: property = LazyProperty(User.from_json)

    # Unused attributes
    # created_at_details: {}
    # spam: bool = kwarg
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
