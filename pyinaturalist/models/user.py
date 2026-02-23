from datetime import datetime

from pyinaturalist.constants import INAT_BASE_URL, JsonResponse, TableRow
from pyinaturalist.models import (
    BaseModel,
    BaseModelCollection,
    datetime_field,
    datetime_now_field,
    define_model,
    define_model_collection,
    field,
)


@define_model
class User(BaseModel):
    """:fa:`user` An iNaturalist user, based on the schema of :v1:`GET /users/{id} <Users/get_users_id>`"""

    activity_count: int = field(
        default=0,
        doc='Combined user activity including observations, identifications, and journal posts',
    )
    annotated_observations_count: int = field(
        default=0, doc='Number of observations the user has annotated'
    )
    created_at: datetime = datetime_now_field(doc='Date and time the user was registered')
    description: str = field(default=None, doc='User profile description')
    faved_project_ids: list[int] = field(factory=list, doc='IDs of projects the user has favorited')
    icon: str = field(default=None, doc='URL for small user icon')
    icon_url: str = field(default=None, doc='URL for medium user icon')
    identifications_count: int = field(default=0, doc='Number of identifications the user has made')
    journal_posts_count: int = field(default=0, doc='Number of journal posts the user has made')
    last_active: datetime = datetime_field(doc='Date and time the user was last active')
    login: str = field(default=None, doc='User login/username')
    monthly_supporter: bool = field(default=None, doc='Indicates if user is a monthly supporter')
    name: str = field(default=None, doc='User real name or display name')
    observations_count: int = field(default=0, doc='Number of observations the user has made')
    orcid: str = field(default=None, doc='ORCID iD')
    preferences: dict = field(factory=dict, doc='User preferences')
    roles: list[str] = field(factory=list, doc='User roles on inaturalist.org')
    site_id: int = field(
        default=None, doc='Site ID for iNaturalist network members, or ``1`` for inaturalist.org'
    )
    species_count: int = field(default=0, doc='Number of unique species the user has observed')
    updated_at: datetime = datetime_now_field(doc='Date and time the user was last updated')

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
    def _row(self) -> TableRow:
        return {
            'ID': self.id,
            'Username': self.username,
            'Display name': self.display_name,
            'Observations': self.observations_count,
            'Identifications': self.identifications_count,
        }

    @property
    def _str_attrs(self) -> list[str]:
        return ['id', 'login', 'name']


@define_model
class UserCount(User):
    """:fa:`user` An iNaturalist user, with an associated count of filtered IDs or observations"""

    count: int = field(default=0, doc='Filtered count for the user')
    observation_count: int = field(default=0, doc="Filtered count for the user's observations")
    species_count: int = field(
        default=0, doc="Filtered count for the user's unique species observed"
    )

    @classmethod
    def from_json(cls, value: JsonResponse, **kwargs) -> 'UserCount':
        """Flatten out count + user fields into a single-level dict before initializing"""
        if 'results' in value:
            value = value['results']
        if 'user' in value:
            value = value.copy()
            value.update(value.pop('user'))
        if 'observation_count' in value and 'count' not in value:
            value['count'] = value['observation_count']
        return super().from_json(value)

    @property
    def _row(self) -> TableRow:
        return {
            'ID': self.id,
            'Username': self.username,
            'Display name': self.display_name,
            'Count': self.count,
        }

    def __str__(self) -> str:
        return super().__str__() + f': {self.count}'


@define_model_collection
class UserCounts(BaseModelCollection):
    """:fa:`user` :fa:`list` A collection of users with an associated counts"""

    data: list[UserCount] = field(factory=list, converter=UserCount.from_json_list)
