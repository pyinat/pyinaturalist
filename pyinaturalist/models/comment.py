from datetime import datetime
from typing import Dict, List

import attr

from pyinaturalist.models import BaseModel, User, cached_property, dataclass, datetime_now_attr, kwarg


@dataclass
class Comment(BaseModel):
    """A dataclass containing information about a comment, matching the schema of observation comments
    from `GET /observations <https://api.inaturalist.org/v1/docs/#!/Observations/get_observations>`_.
    """

    body: str = kwarg
    created_at: datetime = datetime_now_attr
    flags: List = attr.ib(factory=list)
    hidden: bool = kwarg
    id: int = kwarg
    moderator_actions: List = attr.ib(factory=list)
    uuid: str = kwarg

    # Lazy-loaded nested model objects
    _user: Dict = attr.ib(factory=dict, repr=False)
    _user_obj: User = None  # type: ignore

    # Unused attributes
    # created_at_details: Dict = attr.ib(factory=dict)

    @cached_property
    def user(self):
        return User.from_json(self._user)
