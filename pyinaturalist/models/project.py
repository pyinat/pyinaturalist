from datetime import datetime
from typing import Dict, List, Optional

from attr import field

from pyinaturalist.constants import INAT_BASE_URL, Coordinates, JsonResponse, TableRow
from pyinaturalist.models import (
    BaseModel,
    LazyProperty,
    User,
    coordinate_pair,
    datetime_attr,
    datetime_now_attr,
    define_model,
    kwarg,
)
from pyinaturalist.models.observation_field import ObservationField


@define_model
class ProjectObservation(ObservationField):
    """Metadata about an observation that has been added to a project"""

    id: int = kwarg
    preferences: Dict = field(factory=dict)  # Example: {'allows_curator_coordinate_access': True}
    project: Dict = field(factory=dict)  # Example: {'id': 24237}
    user_id: int = kwarg
    uuid: str = kwarg
    user: property = LazyProperty(User.from_json)


@define_model
class ProjectObservationField(ObservationField):
    """An :py:class:`.ObservationField` with additional project-specific information"""

    project_observation_field_id: int = kwarg
    position: int = kwarg
    required: bool = kwarg

    @classmethod
    def from_json(cls, value: JsonResponse, **kwargs) -> 'ProjectObservationField':
        """Flatten out nested values"""
        obs_field = value['observation_field']
        obs_field['project_observation_field_id'] = value['id']
        obs_field['position'] = value['position']
        obs_field['required'] = value['required']
        return super(ProjectObservationField, cls).from_json(obs_field, **kwargs)  # type: ignore


@define_model
class ProjectUser(User):
    """A :py:class:`.User` with additional project-specific information"""

    project_id: int = kwarg
    project_user_id: int = kwarg
    role: str = kwarg

    @classmethod
    def from_json(cls, value: JsonResponse, **kwargs) -> 'ProjectUser':
        """Flatten out nested values"""
        user = value['user']
        user['project_id'] = value['project_id']
        user['project_user_id'] = value['id']
        user['role'] = value['role']
        return super(ProjectUser, cls).from_json(user, **kwargs)  # type: ignore


@define_model
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
    admins: property = LazyProperty(ProjectUser.from_json_list)
    project_observation_fields: property = LazyProperty(ProjectObservationField.from_json_list)
    user: property = LazyProperty(User.from_json)

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

    @property
    def url(self) -> str:
        """Info URL on iNaturalist.org"""
        return f'{INAT_BASE_URL}/projects/{self.id}'

    @property
    def row(self) -> TableRow:
        return {
            'ID': self.id,
            'Title': self.title,
            'Type': self.project_type,
            'URL': self.url,
        }

    def __str__(self) -> str:
        return f'[{self.id}] {self.title}'
