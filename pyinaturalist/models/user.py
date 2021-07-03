from datetime import datetime
from typing import List

from pyinaturalist.constants import INAT_BASE_URL, TableRow
from pyinaturalist.models import BaseModel, datetime_now_field, define_model, field


@define_model
class User(BaseModel):
    """A dataclass containing information about an user, matching the schema of
    `GET /users/{id} <https://api.inaturalist.org/v1/docs/#!/Users/get_users_id>`_.
    """

    activity_count: int = field(default=None)
    created_at: datetime = datetime_now_field(doc='Date and time the user was registered')
    icon: str = field(default=None)
    icon_url: str = field(default=None)
    identifications_count: int = field(default=None)
    journal_posts_count: int = field(default=None)
    login: str = field(default=None)
    name: str = field(default=None)
    observations_count: int = field(default=None)
    orcid: str = field(default=None)
    roles: List = field(factory=list)
    site_id: int = field(default=None)

    # Unused attributes
    # login_autocomplete: str = field(default=None)
    # login_exact: str = field(default=None)
    # name_autocomplete: str = field(default=None)
    # spam: bool = field(default=None)
    # suspended: bool = field(default=None)
    # universal_search_rank: int = field(default=None)

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
