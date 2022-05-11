from abc import abstractmethod

from pyinaturalist.paginator import Paginator


class BaseController:
    """Base class for controllers. A controller provides an interface for all requests related to a
    single resource type. This is mainly for the purpose of splitting up :py:class:`.iNatClient`
    methods by resource type, which keeps code, documentation, and usage more organized and easier
    to navigate.
    """

    def __init__(self, client):
        self.client = client

    @abstractmethod
    def from_ids(self, *object_ids, **params) -> Paginator:
        """Get records by ID"""
