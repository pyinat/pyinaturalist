from datetime import datetime
from typing import List

from pyinaturalist.constants import TableRow
from pyinaturalist.models import (
    BaseModel,
    LazyProperty,
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
    user: property = LazyProperty(User.from_json, type=User, doc='User that added the comment')

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
