"""Placeholder module for backwards-compatibility"""
# flake8: noqa: F401, F403
from typing import List
from warnings import warn

from pyinaturalist.constants import JsonResponse
from pyinaturalist.paginator import paginate_all
from pyinaturalist.v1 import *
from pyinaturalist.v1 import get_observations

msg = (
    'The module `pyinaturalist.node_api` is deprecated; please use `from pyinaturalist import ...`'
)
warn(DeprecationWarning(msg))


def get_all_observations(**params) -> List[JsonResponse]:
    """:fas:`triangle-exclamation` Deprecated; use ``get_observations(page='all')`` instead"""
    msg = "get_all_observations() is deprecated; please use get_observations(page='all') instead"
    warn(DeprecationWarning(msg))
    return paginate_all(get_observations, method='id', **params)['results']
