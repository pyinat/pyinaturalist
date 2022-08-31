from typing import TYPE_CHECKING

from pyinaturalist.paginator import Paginator

if TYPE_CHECKING:
    from pyinaturalist.client import iNatClient


class BaseController:
    """Base class for controllers. A controller provides an interface for all requests related to a
    single resource type. This is mainly for the purpose of splitting up :py:class:`.iNatClient`
    methods by resource type, which keeps code, documentation, and usage more organized and easier
    to navigate.
    """

    def __init__(self, client: 'iNatClient'):
        self.client = client

    def from_ids(self, *object_ids, **params) -> Paginator:
        """Get records by ID"""
        raise NotImplementedError
