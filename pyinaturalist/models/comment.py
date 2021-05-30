from datetime import datetime

from attr import define

from pyinaturalist.models import BaseModel, LazyProperty, User, add_lazy_attrs, datetime_now_attr, kwarg


@define(auto_attribs=False, field_transformer=add_lazy_attrs)
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
