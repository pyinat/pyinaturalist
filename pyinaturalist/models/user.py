from datetime import datetime
from typing import List

from attr import define, field

from pyinaturalist.models import BaseModel, datetime_now_attr, kwarg


@define(auto_attribs=False)
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
    roles: List = field(factory=list)
    site_id: int = kwarg
    spam: bool = kwarg
    suspended: bool = kwarg

    # Unused attributes
    # login_autocomplete: str = kwarg
    # login_exact: str = kwarg
    # name_autocomplete: str = kwarg
    # universal_search_rank: int = kwarg

    # Aliases
    @property
    def username(self) -> str:
        return self.login

    @property
    def display_name(self) -> str:
        return self.name
