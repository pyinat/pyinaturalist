from datetime import datetime
from typing import List

import attr

from pyinaturalist.constants import JsonResponse
from pyinaturalist.models import BaseModel, datetime_now_attr, kwarg


@attr.s
class User(BaseModel):
    """A dataclass containing information about an user, matching the schema of
    `GET /users/{id} <https://api.inaturalist.org/v1/docs/#!/Users/get_users_id>`_.
    """

    activity_count: int = kwarg
    created_at: datetime = datetime_now_attr
    icon: str = kwarg
    icon_url: str = kwarg
    id: int = kwarg
    identifications_count: int = kwarg
    journal_posts_count: int = kwarg
    login: str = kwarg
    name: str = kwarg
    observations_count: int = kwarg
    orcid: str = kwarg
    roles: List = attr.ib(factory=list)
    site_id: int = kwarg
    spam: bool = kwarg
    suspended: bool = kwarg
    universal_search_rank: int = kwarg

    # Unused attributes
    # login_autocomplete: str = kwarg
    # login_exact: str = kwarg
    # name_autocomplete: str = kwarg

    # Aliases
    @property
    def username(self) -> str:
        return self.login

    @property
    def display_name(self) -> str:
        return self.name


@attr.s
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
