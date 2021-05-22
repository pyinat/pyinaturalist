from datetime import datetime
from typing import Dict, List, Optional

from attr import define, field

from pyinaturalist.constants import Coordinates, JsonResponse
from pyinaturalist.models import (
    BaseModel,
    User,
    cached_model_property,
    coordinate_pair,
    datetime_attr,
    datetime_now_attr,
    kwarg,
)
from pyinaturalist.models.observation_field import ObservationField


@define(auto_attribs=False)
class ProjectObservationField(ObservationField):
    """A :py:class:`.ObservationField` with additional project-specific information"""

    project_observation_field_id: int = kwarg
    position: int = kwarg
    required: bool = kwarg

    @classmethod
    def from_project_json(cls, value: JsonResponse, **kwargs):
        """Flatten out nested values"""
        obs_field = value['observation_field']
        obs_field['project_observation_field_id'] = value['id']
        obs_field['position'] = value['position']
        obs_field['required'] = value['required']
        return cls.from_json(obs_field, **kwargs)

    @classmethod
    def from_project_json_list(cls, value: List[JsonResponse], **kwargs):
        return [cls.from_project_json(pof, **kwargs) for pof in value]


@define(auto_attribs=False)
class ProjectUser(User):
    """A :py:class:`.User` with additional project-specific information"""

    project_id: int = kwarg
    project_user_id: int = kwarg
    role: str = kwarg

    @classmethod
    def from_project_json(cls, value: JsonResponse, **kwargs):
        """Flatten out nested values"""
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
    terms: str = kwarg
    title: str = kwarg
    updated_at: Optional[datetime] = datetime_attr
    user_id: int = kwarg

    # Nested collections
    project_observation_rules: List[Dict] = field(factory=list)
    rule_preferences: List[Dict] = field(factory=list)
    search_parameters: List[Dict] = field(factory=list)
    site_features: List[Dict] = field(factory=list)
    user_ids: List[int] = field(factory=list)

    # Lazy-loaded nested model objects
    admins: property = cached_model_property(ProjectUser.from_project_json_list, '_admins')
    _admins: List[Dict] = field(factory=list, repr=False)
    project_observation_fields: property = cached_model_property(
        ProjectObservationField.from_project_json_list, '_project_observation_fields'
    )
    _project_observation_fields: List[Dict] = field(factory=list, repr=False)
    user: property = cached_model_property(User.from_json, '_user')
    _user: Dict = field(default=None, repr=False)

    # Unused attributes
    # flags: List = field(factory=list)
    # latitude: float = kwarg
    # longitude: float = kwarg

    # Aliases
    @property
    def obs_fields(self):
        return self.project_observation_fields

    @property
    def obs_rules(self):
        return self.project_observation_rules


# Alias for a rather verbose class name
POF = ProjectObservationField
