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
class Comment(BaseModel):
    """:fa:`comment` An observation comment, based on the schema of comments
    from `GET /observations <https://api.inaturalist.org/v1/docs/#!/Observations/get_observations>`_.
    """

    body: str = field(default='', doc='Comment text')
    created_at: datetime = datetime_now_field(doc='Date and time the comment was created')
    hidden: bool = field(default=None, doc='Indicates if the comment is hidden')
    uuid: str = field(default=None, doc='Universally unique identifier')
    user: property = LazyProperty(
        User.from_json, type=User, doc='User that added the comment or ID'
    )

    # Unused attributes
    # created_at_details: Dict = field(factory=dict)
    # flags: List = field(factory=list)
    # moderator_actions: List = field(factory=list)

    @property
    def truncated_body(self):
        """Comment text, truncated"""
        truncated_body = self.body.replace('\n', ' ').strip()
        if len(truncated_body) > 50:
            truncated_body = truncated_body[:47].strip() + '...'
        return truncated_body

    @property
    def username(self) -> str:
        return self.user.login

    @property
    def _row(self) -> TableRow:
        return {
            'ID': self.id,
            'User': self.username,
            'Created at': self.created_at,
            'Comment': self.truncated_body,
        }

    @property
    def _str_attrs(self) -> List[str]:
        return ['id', 'username', 'created_at', 'truncated_body']


@define_model
class Identification(Comment):
    """:fa:`fingerprint` An observation identification, based on the schema of
    `GET /identifications <https://api.inaturalist.org/v1/docs/#!/Identifications/get_identifications>`_.
    """

    category: str = field(default=None, options=ID_CATEGORIES, doc='Identification category')
    current: bool = field(
        default=None, doc='Indicates if the identification is the currently accepted one'
    )
    current_taxon: bool = field(default=None)
    disagreement: bool = field(
        default=None, doc='Indicates if this identification disagrees with previous ones'
    )
    own_observation: bool = field(
        default=None, doc='Indicates if the indentifier is also the observer'
    )
    previous_observation_taxon_id: int = field(default=None, doc='Previous observation taxon ID')
    taxon_change: bool = field(default=None)
    vision: bool = field(
        default=None, doc='Indicates if the taxon was selected from computer vision results'
    )
    taxon: property = LazyProperty(Taxon.from_json, type=Taxon, doc='Identification taxon')

    @property
    def taxon_name(self) -> str:
        return self.taxon.full_name

    # Unused attributes
    # created_at_details: {}
    # spam: bool = field(default=None)
    # flags: List = field(factory=list)
    # moderator_actions: List = field(factory=list)
    # observation: {}
    # taxon_id: int = field(default=None)

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
        return ['id', 'username', 'taxon_name', 'created_at', 'truncated_body']
