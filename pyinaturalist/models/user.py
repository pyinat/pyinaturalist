from datetime import datetime
from typing import List

from pyinaturalist.constants import INAT_BASE_URL, TableRow
from pyinaturalist.models import BaseModel, datetime_now_field, define_model, field


@define_model
class User(BaseModel):
    """👤 An iNaturalist user, based on the schema of
    `GET /users/{id} <https://api.inaturalist.org/v1/docs/#!/Users/get_users_id>`_.
    """

    activity_count: int = field(
        default=0,
        doc='Combined user activity including observations, identifications, and journal posts',
    )
    created_at: datetime = datetime_now_field(doc='Date and time the user was registered')
    icon: str = field(default=None, doc='URL for small user icon')
    icon_url: str = field(default=None, doc='URL for medium user icon')
    identifications_count: int = field(default=0, doc='Number of identifications the user has made')
    journal_posts_count: int = field(default=0, doc='Number of journal posts the user has made')
    login: str = field(default=None, doc='User login/username')
    name: str = field(default=None, doc='User real name or display name')
    observations_count: int = field(default=0, doc='Number of observations the user has made')
    orcid: str = field(default=None, doc='ORCID iD')
    roles: List[str] = field(factory=list, doc='User roles on inaturalist.org')
    site_id: int = field(
        default=None, doc='Site ID for iNaturalist network members, or ``1`` for inaturalist.org'
    )
    species_count: int = field(default=0, doc='Number of unique species the user has observed')

    # Unused attributes
    # login_autocomplete: str = field(default=None)
    # login_exact: str = field(default=None)
    # name_autocomplete: str = field(default=None)
    # spam: bool = field(default=None)
    # suspended: bool = field(default=None)
    # universal_search_rank: int = field(default=None)

    @property
    def username(self) -> str:
        """Alias of ``login``"""
        return self.login

    @property
    def display_name(self) -> str:
        """Alias of ``name``"""
        return self.name

    @property
    def url(self) -> str:
        """User info URL on iNaturalist.org"""
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
