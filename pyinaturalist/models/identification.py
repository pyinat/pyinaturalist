from datetime import datetime
from typing import List
from uuid import UUID

import attr

from pyinaturalist.models import BaseModel, Taxon, User, datetime_now_attr, kwarg


@attr.s
class Identification(BaseModel):
    """A dataclass containing information about an identification, matching the schema of
    `GET /identifications <https://api.inaturalist.org/v1/docs/#!/Identifications/get_identifications>`_.
    """

    body: str = kwarg
    category: str = kwarg  # Enum
    created_at: datetime = datetime_now_attr
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

    # Nested model objects
    # observation: {}  # TODO: If this is needed, need to lazy load it
    taxon: Taxon = attr.ib(converter=Taxon.from_json, default=None)  # type: ignore
    user: User = attr.ib(converter=User.from_json, default=None)  # type: ignore

    # Nesetd collections
    flags: List = attr.ib(factory=list)
    moderator_actions: List = attr.ib(factory=list)

    # Unused attributes
    # created_at_details: {}
