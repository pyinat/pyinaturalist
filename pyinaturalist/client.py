# TODO: "optional auth" option
# TODO: Improve Sphinx docs generated for controller attributes
# TODO: Use a custom template or directive to generate summary of all controller methods
from asyncio import AbstractEventLoop
from collections.abc import Callable
from inspect import ismethod
from logging import getLogger
from typing import Any

from pyinaturalist.auth import get_access_token, get_access_token_via_auth_code
from pyinaturalist.constants import RequestParams
from pyinaturalist.controllers import (
    AnnotationController,
    IdentificationController,
    ObservationController,
    ObservationFieldController,
    PlaceController,
    ProjectController,
    SearchController,
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

    See:

    * Usage guide: :ref:`api-client`
    * Query functions: :ref:`Controller classes <controllers>`

    Controllers (for separate API resource types):

    * :fa:`tag` :py:class:`annotations <.AnnotationController>`
    * :fa:`fingerprint` :py:class:`identifications <.IdentificationController>`
    * :fa:`binoculars` :py:class:`observations <.ObservationController>`
    * :fa:`tag` :py:class:`observation_fields <.ObservationFieldController>`
    * :fa:`location-dot` :py:class:`places <.PlaceController>`
    * :fa:`users` :py:class:`projects <.ProjectController>`
    * :fa:`search` :py:class:`search <.SearchController>`
    * :fa:`dove` :py:class:`taxa <.TaxonController>`
    * :fa:`user` :py:class:`users <.UserController>`

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
        creds: dict[str, str] | None = None,
        default_params: dict[str, Any] | None = None,
        dry_run: bool = False,
        loop: AbstractEventLoop | None = None,
        session: ClientSession | None = None,
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
        self.identifications = IdentificationController(
            self
        )  #: Interface for :py:class:`identification requests <.IdentificationController>`
        self.observations = ObservationController(
            self
        )  #: Interface for :py:class:`observation requests <.ObservationController>`
        self.observation_fields = ObservationFieldController(
            self
        )  #: Interface for :py:class:`observation field requests <.ObservationFieldController>`
        self.places = PlaceController(
            self
        )  #: Interface for :py:class:`place requests <.PlaceController>`
        self.projects = ProjectController(
            self
        )  #: Interface for :py:class:`project requests <.ProjectController>`
        self.search = SearchController(
            self
        )  #: Unified :py:meth:`text search <.SearchController.__call__>`
        self.taxa = TaxonController(
            self
        )  #: Interface for :py:class:`taxon requests <.TaxonController>`
        self.users = UserController(
            self
        )  #: Interface for :py:class:`user requests <.UserController>`

    def add_defaults(
        self, request_function, kwargs: RequestParams | None = None, auth: bool = False
    ) -> RequestParams:
        """Add any applicable client settings to request parameters before sending a request.
        Explicit keyword arguments will override any client settings.
        """
        kwargs = strip_empty_values(kwargs or {})
        client_kwargs = {'dry_run': self.dry_run, 'session': self.session}

        # Add access token if needed
        if auth:
            if self.creds.get('auth_flow') == 'authorization_code':
                auth_code_creds = {k: v for k, v in self.creds.items() if k != 'auth_flow'}
                client_kwargs['access_token'] = get_access_token_via_auth_code(**auth_code_creds)  # type: ignore
            else:
                access_token = kwargs.pop('access_token', None) or get_access_token(**self.creds)  # type: ignore
                client_kwargs['access_token'] = access_token

        # Add default request parameters if applicable
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
        model: type[T],
        auth: bool = False,
        cls: type[Paginator] = Paginator,
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
        kwargs = self.add_defaults(request_function, kwargs, auth)
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
        kwargs = self.add_defaults(request_function, kwargs, auth)
        return request_function(*args, **kwargs)
