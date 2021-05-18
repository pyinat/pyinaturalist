import attr
from datetime import datetime
from typing import List

from pyinaturalist.models import BaseModel, aliased_kwarg, kwarg, timestamp


@attr.s
class User(BaseModel):
    activity_count: int = kwarg
    created_at: datetime = timestamp
    display_name: str = kwarg
    icon: str = kwarg
    icon_url: str = kwarg
    identifications_count: int = kwarg
    journal_posts_count: int = kwarg
    login: str = aliased_kwarg  # Aliased to 'username'
    name: str = aliased_kwarg  # Aliased to 'display_name'
    observations_count: int = kwarg
    orcid: str = kwarg
    roles: List = attr.ib(factory=list)
    site_id: int = kwarg
    spam: bool = kwarg
    suspended: bool = kwarg
    universal_search_rank: int = kwarg
    username: str = kwarg

    # Additional response fields that are used by the web UI but are redundant here
    # login_autocomplete: str = kwarg
    # login_exact: str = kwarg
    # name_autocomplete: str = kwarg

    # Add aliases
    def __attrs_post_init__(self):
        self.username = self.login
        self.display_name = self.name
