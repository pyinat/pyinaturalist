from datetime import datetime
from typing import Dict, List, Optional

from attr import define, field

from pyinaturalist.constants import Coordinates, JsonResponse
from pyinaturalist.models import (
    BaseModel,
    User,
    coordinate_pair,
    datetime_attr,
    datetime_now_attr,
    kwarg,
)


@define(auto_attribs=False)
class ProjectUser(User):
    """A :py:class:`.User` with additional project-specific information returned by
    `GET /projects <https://api.inaturalist.org/v1/docs/#!/Projects/get_projects>`_.
    """

    project_id: int = kwarg
    project_user_id: int = kwarg
    role: str = kwarg

    @classmethod
    def from_project_json(cls, value: JsonResponse, **kwargs):
        """Flatten out nested values from project user info"""
        user = value['user']
        user['project_id'] = value['project_id']
        user['project_user_id'] = value['id']
        user['role'] = value['role']
        return cls.from_json(user, **kwargs)

    @classmethod
    def from_project_json_list(cls, value: List[JsonResponse], **kwargs):
        return [cls.from_project_json(project_user, **kwargs) for project_user in value]


@define(auto_attribs=False)
class Project(BaseModel):
    """A dataclass containing information about a project, matching the schema of
    `GET /projects <https://api.inaturalist.org/v1/docs/#!/Projects/get_projects>`_.
    """

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
    admins: List[ProjectUser] = field(converter=ProjectUser.from_project_json_list, factory=list)  # type: ignore
    user: User = field(converter=User.from_json, default=None)  # type: ignore

    # Nested collections
    flags: List = field(factory=list)  # TODO: Unsure of list type. str?
    project_observation_fields: List = field(factory=list)  # TODO: Unsure of list type. dict?
    project_observation_rules: List = field(factory=list)
    rule_preferences: List[Dict] = field(factory=list)
    search_parameters: List[Dict] = field(factory=list)
    site_features: List[Dict] = field(factory=list)
    user_ids: List[int] = field(factory=list)

    # Unused attributes
    # latitude: float = kwarg
    # longitude: float = kwarg
