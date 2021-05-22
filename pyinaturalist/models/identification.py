from datetime import datetime
from typing import Dict

from attr import define, field

from pyinaturalist.models import BaseModel, Taxon, User, cached_model_property, datetime_now_attr, kwarg


@define(auto_attribs=False)
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
    taxon_change: bool = kwarg  # TODO: confirm type
    taxon_id: int = kwarg
    uuid: str = kwarg
    vision: bool = kwarg

    # Lazy-loaded nested model objects
    taxon: property = cached_model_property(Taxon.from_json, '_taxon')
    _taxon: Dict = field(default=None, repr=False)
    user: property = cached_model_property(User.from_json, '_user')
    _user: Dict = field(default=None, repr=False)

    # Unused attributes
    # created_at_details: {}
    # spam: bool = kwarg
    # flags: List = field(factory=list)
    # moderator_actions: List = field(factory=list)
    # observation: {}  # TODO: Is this actually needed?


ID = Identification
