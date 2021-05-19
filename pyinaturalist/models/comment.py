from datetime import datetime
from typing import List

import attr

from pyinaturalist.models import BaseModel, User, datetime_now_attr, kwarg


@attr.s
class Comment(BaseModel):
    moderator_actions: List = attr.ib(factory=list)
    hidden: bool = kwarg
    flags: List = attr.ib(factory=list)
    created_at: datetime = datetime_now_attr
    id: int = kwarg
    body: str = kwarg
    uuid: str = kwarg
    user: User = attr.ib(converter=User.from_json, default=None)

    # Redundant attributes
    # created_at_details: {date: 2020-08-28, week: 35, month: 8, hour: 12, year: 2020, day: 28},
