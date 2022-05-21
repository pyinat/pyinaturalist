from datetime import datetime
from typing import Dict, List

from pyinaturalist.constants import (
    INAT_BASE_URL,
    PROJECT_TYPES,
    Coordinates,
    DateTime,
    JsonResponse,
    TableRow,
)
from pyinaturalist.models import (
    BaseModel,
    LazyProperty,
    ObservationField,
    User,
    coordinate_pair,
    datetime_field,
    datetime_now_field,
    define_model,
    field,
)


@define_model
class ProjectObservation(BaseModel):
    """:fa:`binoculars` Metadata about an observation that has been added to a project"""

    preferences: Dict = field(factory=dict)  # Example: {'allows_curator_coordinate_access': True}
    project: Dict = field(factory=dict)  # Example: {'id': 24237}
    user_id: int = field(default=None)
    uuid: str = field(default=None, doc='Universally unique identifier')
    user: property = LazyProperty(
        User.from_json, type=User, doc='User that added the observation to the project'
    )

    @property
    def _str_attrs(self) -> List[str]:
        return ['project', 'user_id']


@define_model
class ProjectObservationField(ObservationField):
    """:fa:`tag` An :py:class:`.ObservationField` with additional project-specific information"""

    project_observation_field_id: int = field(default=None)
    position: int = field(default=None)
    required: bool = field(default=None)

    @classmethod
    def from_json(cls, value: JsonResponse, **kwargs) -> 'ProjectObservationField':
        """Flatten out nested values"""
        obs_field = value['observation_field']
        obs_field['project_observation_field_id'] = value['id']
        obs_field['position'] = value['position']
        obs_field['required'] = value['required']
        return super(ProjectObservationField, cls).from_json(obs_field, **kwargs)

    @property
    def _str_attrs(self) -> List[str]:
        return ['project_observation_field_id', 'required']


@define_model
class ProjectUser(User):
    """:fa:`user` A :py:class:`.User` with additional project-specific information"""

    project_id: int = field(default=None)
    project_user_id: int = field(default=None)
    role: str = field(default=None)

    @classmethod
    def from_json(cls, value: JsonResponse, **kwargs) -> 'ProjectUser':
        """Flatten out nested values"""
        user = value['user']
        user['project_id'] = value['project_id']
        user['project_user_id'] = value['id']
        user['role'] = value['role']
        return super(ProjectUser, cls).from_json(user, **kwargs)

    @property
    def _str_attrs(self) -> List[str]:
        return ['project_id', 'project_user_id', 'role']


@define_model
class Project(BaseModel):
    """:fa:`users` An iNaturalist project, based on the schema of
    `GET /projects <https://api.inaturalist.org/v1/docs/#!/Projects/get_projects>`_.
    """

    banner_color: str = field(default=None)
    created_at: datetime = datetime_now_field(doc='Date and time the project was created')
    description: str = field(default=None, doc='Project description')
    header_image_url: str = field(default=None)
    hide_title: bool = field(default=None)
    icon: str = field(default=None, doc='URL for project icon')
    is_umbrella: bool = field(
        default=None,
        doc='Indicates if this is an umbrella project (containing observations from other projects)',
    )
    location: Coordinates = coordinate_pair()
    place_id: int = field(default=None, doc='Project place ID')
    prefers_user_trust: bool = field(
        default=None,
        doc='Indicates if the project wants users to share hidden coordinates with the project admins',
    )
    project_observation_rules: List[Dict] = field(factory=list, doc='Project observation rules')
    project_type: str = field(default=None, options=PROJECT_TYPES, doc='Project type')  # Enum
    rule_preferences: List[Dict] = field(factory=list)
    search_parameters: List[Dict] = field(factory=list, doc='Filters for observations to include')
    site_features: List[Dict] = field(
        factory=list, doc='Details about if/when the project was featured on inaturalist.org'
    )
    slug: str = field(default=None, doc='URL slug')
    terms: str = field(default=None, doc='Project terms')
    title: str = field(default=None, doc='Project title')
    updated_at: DateTime = datetime_field(doc='Date and time the project was last updated')
    user_ids: List[int] = field(factory=list)

    # Lazy-loaded model objects
    admins: property = LazyProperty(
        ProjectUser.from_json_list, type=List[User], doc='Project admin users'
    )
    project_observation_fields: property = LazyProperty(
        ProjectObservationField.from_json_list,
        type=List[ProjectObservationField],
        doc='Observation fields used by the project',
    )
    user: property = LazyProperty(User.from_json, type=User, doc='User that created the project')

    # Unused attributes
    # flags: List = field(factory=list)
    # header_image_contain: bool = field(default=None)
    # header_image_file_name: str = field(default=None)
    # icon_file_name: str = field(default=None)
    # latitude: float = field(default=None)
    # longitude: float = field(default=None)
    # user_id: int = field(default=None)

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
    def _row(self) -> TableRow:
        return {
            'ID': self.id,
            'Title': self.title,
            'Type': self.project_type,
            'URL': self.url,
        }

    @property
    def _str_attrs(self) -> List[str]:
        return ['id', 'title']
