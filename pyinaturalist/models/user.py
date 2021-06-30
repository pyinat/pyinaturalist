from datetime import datetime
from typing import List

from attr import field

from pyinaturalist.constants import INAT_BASE_URL, TableRow
from pyinaturalist.models import BaseModel, datetime_now_attr, define_model, kwarg


@define_model
class User(BaseModel):
    """A dataclass containing information about an user, matching the schema of
    `GET /users/{id} <https://api.inaturalist.org/v1/docs/#!/Users/get_users_id>`_.
    """

    activity_count: int = kwarg
    created_at: datetime = datetime_now_attr
    icon: str = kwarg
    icon_url: str = kwarg
    identifications_count: int = kwarg
    journal_posts_count: int = kwarg
    login: str = kwarg
    name: str = kwarg
    observations_count: int = kwarg
    orcid: str = kwarg
    roles: List = field(factory=list)
    site_id: int = kwarg

    # Unused attributes
    # login_autocomplete: str = kwarg
    # login_exact: str = kwarg
    # name_autocomplete: str = kwarg
    # spam: bool = kwarg
    # suspended: bool = kwarg
    # universal_search_rank: int = kwarg

    # Aliases
    @property
    def username(self) -> str:
        return self.login

    @property
    def display_name(self) -> str:
        return self.name

    @property
    def url(self) -> str:
        """Info URL on iNaturalist.org"""
        return f'{INAT_BASE_URL}/users/{self.id}'

    @property
    def row(self) -> TableRow:
        return {
            'ID': self.id,
            'Username': self.username,
            'Display name': self.display_name,
            'Obs. count': self.observations_count,
            'ID count': self.identifications_count,
        }

    def __str__(self) -> str:
        real_name = f' ({self.name})' if self.name else ''
        return f"[{self.id}] {self.login}{real_name}"
