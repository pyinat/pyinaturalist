from datetime import datetime
from typing import Dict, List, Optional

import attr

from pyinaturalist.constants import Coordinates
from pyinaturalist.models import (
    BaseModel,
    ProjectUser,
    User,
    coordinate_pair,
    datetime_attr,
    datetime_now_attr,
    kwarg,
)


@attr.s
class Project(BaseModel):
    banner_color: str = kwarg
    created_at: datetime = datetime_now_attr
    description: str = kwarg
    header_image_contain: bool = kwarg
    header_image_file_name: str = kwarg
    header_image_url: str = kwarg
    hide_title: bool = kwarg
    icon_file_name: str = kwarg
    icon: str = kwarg
    id: int = kwarg
    is_umbrella: bool = kwarg
    location: Optional[Coordinates] = coordinate_pair
    place_id: int = kwarg
    prefers_user_trust: bool = kwarg
    project_type: str = kwarg
    slug: str = kwarg
    terms: str = kwarg  # TODO: Unsure of type
    title: str = kwarg
    updated_at: Optional[datetime] = datetime_attr
    user_id: int = kwarg

    # Nested model objects
    admins: List[ProjectUser] = attr.ib(converter=ProjectUser.from_project_json_list, factory=list)  # type: ignore
    user: User = attr.ib(converter=User.from_json, default=None)  # type: ignore

    # Nested collections
    flags: List = attr.ib(factory=list)  # TODO: Unsure of list type. str?
    project_observation_fields: List = attr.ib(factory=list)  # TODO: Unsure of list type. dict?
    project_observation_rules: List = attr.ib(factory=list)
    rule_preferences: List[Dict] = attr.ib(factory=list)
    search_parameters: List[Dict] = attr.ib(factory=list)
    site_features: List[Dict] = attr.ib(factory=list)
    user_ids: List[int] = attr.ib(factory=list)

    # TODO: Redundant with location. Exclude?
    # latitude: float = kwarg
    # longitude: float = kwarg
