# TODO: "optional auth" option
# TODO: Improve Sphinx docs generated for controller attributes
# TODO: Use a custom template or directive to generate summary of all controller methods
from asyncio import AbstractEventLoop
from inspect import ismethod
from logging import getLogger
from typing import Any, Callable, Dict, Optional, Type

from requests import Session

from pyinaturalist.auth import get_access_token
from pyinaturalist.constants import RequestParams
from pyinaturalist.controllers import (
    AnnotationController,
    ObservationController,
    PlaceController,
    ProjectController,
    TaxonController,
    UserController,
)
from pyinaturalist.models import T
from pyinaturalist.paginator import Paginator
from pyinaturalist.request_params import get_valid_kwargs, strip_empty_values
from pyinaturalist.session import ClientSession

logger = getLogger(__name__)


# 'iNatClient' is nonstandard casing, but 'InatClient' just looks wrong. Deal with it, pep8.
class iNatClient:
    """API client class that provides an object-oriented interface to the iNaturalist API.

    **WIP/Experimental**

    See:

    * Usage guide: :ref:`api-client`
    * Query functions: :ref:`Controller classes <controllers>`

    Controllers:

    * :py:class:`annotations <.AnnotationController>`
    * :py:class:`observations <.ObservationController>`
    * :py:class:`places <.PlaceController>`
    * :py:class:`projects <.ProjectController>`
    * :py:class:`taxa <.TaxonController>`
    * :py:class:`users <.UserController>`

    Args:
        creds: Optional arguments for :py:func:`.get_access_token`, used to get and refresh access
            tokens as needed. Using a keyring instead is recommended, though.
        default_params: Default request parameters to pass to any applicable API requests
        dry_run: Just log all requests instead of sending real requests
        loop: An event loop to run any executors used for async iteration
        session: Session object to use instead of creating a new one
        kwargs: Keyword arguments for :py:class:`.ClientSession`
    """

    def __init__(
        self,
        creds: Optional[Dict[str, str]] = None,
        default_params: Optional[Dict[str, Any]] = None,
        dry_run: bool = False,
        loop: Optional[AbstractEventLoop] = None,
        session: Optional[Session] = None,
        **kwargs,
    ):
        self.creds = creds or {}
        self.default_params = default_params or {}
        self.dry_run = dry_run
        self.loop = loop
        self.session = session or ClientSession(**kwargs)

        self._access_token = None
        self._token_expires = None

        # Controllers
        self.annotations = AnnotationController(
            self
        )  #: Interface for :py:class:`annotation requests <.AnnotationController>`
        self.observations = ObservationController(
            self
        )  #: Interface for :py:class:`observation requests <.ObservationController>`
        self.places = PlaceController(
            self
        )  #: Interface for :py:class:`place requests <.PlaceController>`
        self.projects = ProjectController(
            self
        )  #: Interface for :py:class:`project requests <.ProjectController>`
        self.taxa = TaxonController(
            self
        )  #: Interface for :py:class:`taxon requests <.TaxonController>`
        self.users = UserController(
            self
        )  #: Interface for :py:class:`user requests <.UserController>`

    def add_client_settings(
        self, request_function, kwargs: Optional[RequestParams] = None, auth: bool = False
    ) -> RequestParams:
        """Add any applicable client settings to request parameters before sending a request.
        Explicit keyword arguments will override any client settings.
        """
        kwargs = strip_empty_values(kwargs or {})
        client_kwargs = {'dry_run': self.dry_run, 'session': self.session}

        # Add access token and default params, if applicable
        if auth:
            client_kwargs['access_token'] = get_access_token(**self.creds)  # type: ignore
        client_kwargs.update(get_valid_kwargs(request_function, self.default_params))
        for k, v in client_kwargs.items():
            kwargs.setdefault(k, v)

        # If we're directly calling a ClientSession method, we don't need to pass a session object
        if ismethod(request_function):
            kwargs.pop('session')

        return kwargs

    def paginate(
        self,
        request_function: Callable,
        model: Type[T],
        auth: bool = False,
        cls: Type[Paginator] = Paginator,
        **kwargs,
    ) -> Paginator[T]:
        """Create a paginator for a request, with client settings applied

        Args:
            request_function: The API request function to call
            model: Model class used for the response
            auth: Indicates that the request requires authentication
            cls: Alternative Paginator class to use
            params: Original request parameters
        """
        kwargs = self.add_client_settings(request_function, kwargs, auth)
        return cls(request_function, model, loop=self.loop, **kwargs)

    def request(self, request_function: Callable, *args, auth: bool = False, **kwargs):
        """Send a request, with client settings applied.

        Args:
            request_function: The API request function to call
            auth: Indicates that the request requires authentication
            params: Original request parameters

        Returns:
            Results of ``request_function()``
        """
        kwargs = self.add_client_settings(request_function, kwargs, auth)
        return request_function(*args, **kwargs)
