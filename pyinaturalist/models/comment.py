from datetime import datetime
from typing import List

import attr

from pyinaturalist.models import BaseModel, User, dataclass, datetime_now_attr, kwarg


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

    # Nested model objects
    user: User = attr.ib(converter=User.from_json, default=None)  # type: ignore

    # Unused attributes
    # created_at_details: {date: 2020-08-28, week: 35, month: 8, hour: 12, year: 2020, day: 28},
