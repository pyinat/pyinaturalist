from datetime import datetime

from pyinaturalist.constants import TableRow
from pyinaturalist.models import BaseModel, LazyProperty, User, datetime_now_attr, define_model, kwarg


@define_model
class Comment(BaseModel):
    """An observation comment, based on the schema of comments
    from `GET /observations <https://api.inaturalist.org/v1/docs/#!/Observations/get_observations>`_.
    """

    body: str = kwarg
    created_at: datetime = datetime_now_attr
    hidden: bool = kwarg
    uuid: str = kwarg

    # Lazy-loaded nested model objects
    user: property = LazyProperty(User.from_json)

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
