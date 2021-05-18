from datetime import datetime
from typing import List
from uuid import UUID

import attr

from pyinaturalist.models import BaseModel, Taxon, User, aliased_kwarg, created_timestamp, kwarg


@attr.s
class Identification(BaseModel):
    body: str = aliased_kwarg  # Aliased to 'comment'
    category: str = kwarg  # Enum
    comment: str = kwarg
    created_at: datetime = created_timestamp
    current: bool = kwarg
    current_taxon: bool = kwarg
    disagreement: bool = kwarg
    hidden: bool = kwarg
    id: int = kwarg
    own_observation: bool = kwarg
    previous_observation_taxon_id: int = kwarg
    spam: bool = kwarg
    taxon_change: bool = kwarg  # TODO: confirm type
    taxon_id: int = kwarg
    uuid: UUID = attr.ib(converter=UUID, default=None)
    vision: bool = kwarg

    flags: List = attr.ib(factory=list)
    moderator_actions: List = attr.ib(factory=list)
    # observation: {}  # TODO: If this is needed, need to lazy load it
    taxon: Taxon = attr.ib(converter=Taxon.from_json, default=None)
    user: User = attr.ib(converter=User.from_json, default=None)

    # created_at_details: {}
