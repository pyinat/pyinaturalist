# TODO: "optional auth" option
# TODO: Improve Sphinx docs generated for controller attributes
# TODO: Use a custom template or directive to generate summary of all controller methods
from asyncio import AbstractEventLoop
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from inspect import ismethod
from logging import getLogger
from typing import Any, Literal

from requests import HTTPError

from pyinaturalist.auth import _decode_jwt_exp, get_access_token, get_access_token_via_auth_code
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
from pyinaturalist.exceptions import AuthenticationError
from pyinaturalist.models import T
from pyinaturalist.paginator import Paginator
from pyinaturalist.request_params import get_valid_kwargs, strip_empty_values
from pyinaturalist.session import ClientSession

logger = getLogger(__name__)


@dataclass
class _TokenInfo:
    """Internal record of a fetched access token and its metadata."""

    token: str
    obtained_at: datetime  # UTC datetime when the token was fetched
    flow: Literal['password', 'authorization_code']
    expires_at: datetime | None  # decoded from JWT exp claim; None for non-JWT tokens


AUTH_CODE_CRED_KEYS = frozenset(
    {
        'app_id',
        'app_secret',
        'use_pkce',
        'use_oob',
        'jwt',
        'refresh',
        'port',
        'timeout',
        'open_url',
        'get_code',
        # Note: 'auth_flow' is intentionally excluded — it's a client-level key, not a
        # parameter accepted by get_access_token_via_auth_code().
    }
)

PASSWORD_FLOW_CRED_KEYS = frozenset(
    {'username', 'password', 'app_id', 'app_secret', 'jwt', 'refresh'}
)

SUPPORTED_AUTH_FLOWS = frozenset({'password', 'authorization_code'})


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
        creds: Optional arguments for :py:func:`.get_access_token` or
            :py:func:`.get_access_token_via_auth_code`, used to get and refresh access
            tokens as needed. Use ``auth_flow='authorization_code'`` to select authorization code
            flow; otherwise password flow is used.
        default_params: Default request parameters to pass to any applicable API requests
        dry_run: Just log all requests instead of sending real requests
        loop: An event loop to run any executors used for async iteration
        session: Session object to use instead of creating a new one
        kwargs: Keyword arguments for :py:class:`.ClientSession`
    """

    def __init__(
        self,
        creds: dict[str, Any] | None = None,
        default_params: dict[str, Any] | None = None,
        dry_run: bool = False,
        loop: AbstractEventLoop | None = None,
        session: ClientSession | None = None,
        **kwargs,
    ):
        self.creds = creds or {}
        auth_flow = self.creds.get('auth_flow')
        if auth_flow is not None and auth_flow not in SUPPORTED_AUTH_FLOWS:
            raise AuthenticationError(
                f'Unsupported auth_flow {auth_flow!r}. '
                f'Accepted values: {sorted(SUPPORTED_AUTH_FLOWS)}'
            )
        self.default_params = default_params or {}
        self.dry_run = dry_run
        self.loop = loop
        self.session = session or ClientSession(**kwargs)
        self._token_info: _TokenInfo | None = None

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
            access_token = self._resolve_access_token(kwargs)
            if access_token:
                client_kwargs['access_token'] = access_token

        # Add default request parameters if applicable
        client_kwargs.update(get_valid_kwargs(request_function, self.default_params))
        for k, v in client_kwargs.items():
            kwargs.setdefault(k, v)

        # If we're directly calling a ClientSession method, we don't need to pass a session object
        if ismethod(request_function):
            kwargs.pop('session')

        return kwargs

    def _resolve_access_token(self, kwargs: RequestParams) -> str | None:
        """Resolve an access token from request args, client cache, or credentials."""
        access_token = kwargs.pop('access_token', None)
        if access_token:
            return access_token
        if self._token_info:
            still_valid = self._token_info.expires_at is None or self._token_info.expires_at > (
                datetime.now(tz=timezone.utc) + timedelta(seconds=60)
            )
            if still_valid:
                return self._token_info.token
            # Token is expired or about to expire — fall through to re-fetch
            self._token_info = None
        self._token_info = self._fetch_access_token_from_creds()
        return self._token_info.token

    def _fetch_access_token_from_creds(self, force_refresh: bool = False) -> _TokenInfo:
        """Get a new access token from configured credentials and wrap it in _TokenInfo."""
        flow = self.creds.get('auth_flow', 'password')
        if flow == 'authorization_code':
            auth_code_creds = self._filter_auth_code_creds(self.creds)
            if force_refresh:
                auth_code_creds['refresh'] = True
            token = get_access_token_via_auth_code(**auth_code_creds)
        else:
            token_creds = {k: v for k, v in self.creds.items() if k in PASSWORD_FLOW_CRED_KEYS}
            if force_refresh:
                token_creds['refresh'] = True
            token = get_access_token(**token_creds)

        return _TokenInfo(
            token=token,
            obtained_at=datetime.now(tz=timezone.utc),
            flow=flow,
            expires_at=_decode_jwt_exp(token),
        )

    @staticmethod
    def _filter_auth_code_creds(creds: dict[str, Any]) -> dict[str, Any]:
        """Keep only credentials accepted by get_access_token_via_auth_code()."""
        return {k: v for k, v in creds.items() if k in AUTH_CODE_CRED_KEYS}

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
        explicit_access_token = kwargs.get('access_token') is not None
        kwargs = self.add_defaults(request_function, kwargs, auth)
        try:
            return request_function(*args, **kwargs)
        except HTTPError as e:
            if not auth or explicit_access_token or not self._is_unauthorized_error(e):
                raise
            self._token_info = self._fetch_access_token_from_creds(force_refresh=True)
            kwargs = kwargs.copy()
            kwargs['access_token'] = self._token_info.token
            return request_function(*args, **kwargs)

    @staticmethod
    def _is_unauthorized_error(error: HTTPError) -> bool:
        response = getattr(error, 'response', None)
        return bool(response is not None and response.status_code == 401)
