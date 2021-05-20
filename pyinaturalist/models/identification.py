from datetime import datetime
from typing import Dict, List

import attr

from pyinaturalist.models import (
    BaseModel,
    Taxon,
    User,
    cached_property,
    dataclass,
    datetime_now_attr,
    kwarg,
)


@dataclass
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
    uuid: str = kwarg
    vision: bool = kwarg

    # Lazy-loaded nested model objects
    # observation: {}  # TODO: Is this actually needed?
    _taxon: Dict = attr.ib(factory=dict, repr=False)
    _taxon_obj: Taxon = None  # type: ignore
    _user: Dict = attr.ib(factory=dict, repr=False)
    _user_obj: User = None  # type: ignore

    # Nesetd collections
    flags: List = attr.ib(factory=list)
    moderator_actions: List = attr.ib(factory=list)

    # Unused attributes
    # created_at_details: {}

    @cached_property
    def taxon(self):
        return Taxon.from_json(self._taxon)

    @cached_property
    def user(self):
        return User.from_json(self._user)


ID = Identification
