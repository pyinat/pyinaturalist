"""Placeholder module for backwards-compatibility"""
# flake8: noqa: F401, F403
from warnings import warn

from pyinaturalist.auth import get_access_token
from pyinaturalist.constants import ListResponse
from pyinaturalist.paginator import paginate_all
from pyinaturalist.v0 import *

msg = (
    'The module `pyinaturalist.rest_api` is deprecated; please use `from pyinaturalist import ...`'
)
warn(DeprecationWarning(msg))


def get_all_observation_fields(**params) -> ListResponse:
    """:fas:`triangle-exclamation` Deprecated; use ``get_observation_fields(page='all')`` instead"""
    msg = "get_all_observation_fields() is deprecated; please use get_observation_fields(page='all') instead"
    warn(DeprecationWarning(msg))
    return paginate_all(get_observation_fields, method='page', **params)['results']


def add_photo_to_observation(*args, **kwargs):
    return upload_photos(*args, **kwargs)
