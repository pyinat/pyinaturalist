from datetime import datetime
from typing import Dict, List

from attr import define, field

from pyinaturalist.models import BaseModel, User, cached_model_property, datetime_now_attr, kwarg


@define(auto_attribs=False)
class Comment(BaseModel):
    """A dataclass containing information about a comment, matching the schema of observation comments
    from `GET /observations <https://api.inaturalist.org/v1/docs/#!/Observations/get_observations>`_.
    """

    body: str = kwarg
    created_at: datetime = datetime_now_attr
    flags: List = field(factory=list)
    hidden: bool = kwarg
    id: int = kwarg
    moderator_actions: List = field(factory=list)
    uuid: str = kwarg

    # Lazy-loaded nested model objects
    user: property = cached_model_property(User.from_json, '_user')
    _user: Dict = field(factory=dict, repr=False)

    # Unused attributes
    # created_at_details: Dict = field(factory=dict)
