from datetime import datetime

from pyinaturalist.constants import TableRow
from pyinaturalist.models import BaseModel, LazyProperty, User, datetime_now_field, define_model, field


@define_model
class Comment(BaseModel):
    """📝 An observation comment, based on the schema of comments
    from `GET /observations <https://api.inaturalist.org/v1/docs/#!/Observations/get_observations>`_.
    """

    body: str = field(default=None, doc='Comment text')
    created_at: datetime = datetime_now_field(doc='Date and time the comment was created')
    hidden: bool = field(default=None, doc='Indicates if the comment is hidden')
    uuid: str = field(default=None, doc='Universally unique identifier')
    user: property = LazyProperty(User.from_json, type=User, doc='User that added the comment')

    # Unused attributes
    # created_at_details: Dict = field(factory=dict)
    # flags: List = field(factory=list)
    # moderator_actions: List = field(factory=list)

    @property
    def row(self) -> TableRow:
        return {
            'ID': self.id,
            'User': self.user.login,
            'Created at': self.created_at,
            'Comment': self.body,
        }

    def __str__(self) -> str:
        return f'{self.user.login} at {self.created_at}: {self.body}'
