from datetime import datetime

from pyinaturalist.models import BaseModel, LazyProperty, User, datetime_now_attr, define_model, kwarg


@define_model
class Comment(BaseModel):
    """A dataclass containing information about a comment, matching the schema of observation comments
    from `GET /observations <https://api.inaturalist.org/v1/docs/#!/Observations/get_observations>`_.
    """

    body: str = kwarg
    created_at: datetime = datetime_now_attr
    hidden: bool = kwarg
    id: int = kwarg
    uuid: str = kwarg

    # Lazy-loaded nested model objects
    user: property = LazyProperty(User.from_json)

    # Unused attributes
    # created_at_details: Dict = field(factory=dict)
    # flags: List = field(factory=list)
    # moderator_actions: List = field(factory=list)

    def __str__(self) -> str:
        return f'{self.user.login} at {self.created_at}: {self.body}'
