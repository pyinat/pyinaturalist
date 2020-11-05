"""
Code used to access the (read/write, but slow) Rails based API of iNaturalist
See: https://www.inaturalist.org/pages/api+reference

Functions
---------

.. automodsumm:: pyinaturalist.rest_api
    :functions-only:
    :nosignatures:

"""
from os import getenv
from time import sleep
from typing import Dict, Any, List, Union

from pyinaturalist import api_docs as docs
from pyinaturalist.constants import (
    THROTTLING_DELAY,
    INAT_BASE_URL,
    FileOrPath,
    JsonResponse,
    ListResponse,
    RequestParams,
)
from pyinaturalist.exceptions import AuthenticationError, ObservationNotFound
from pyinaturalist.api_requests import delete, get, post, put
from pyinaturalist.forge_utils import document_request_params
from pyinaturalist.request_params import (
    OBSERVATION_FORMATS,
    REST_OBS_ORDER_BY_PROPERTIES,
    check_deprecated_params,
    convert_observation_fields,
    ensure_file_obj,
    ensure_file_objs,
    validate_multiple_choice_param,
    warn,
)
from pyinaturalist.response_format import convert_lat_long_to_float


def get_access_token(
    username: str = None,
    password: str = None,
    app_id: str = None,
    app_secret: str = None,
    user_agent: str = None,
) -> str:
    """Get an access token using the user's iNaturalist username and password.
    You still need an iNaturalist app to do this.

    **API reference:** https://www.inaturalist.org/pages/api+reference#auth

    **Environment Variables**

    Alternatively, you may provide credentials via environment variables instead. The
    environment variable names are the keyword arguments in uppercase, prefixed with ``INAT_``:

    * ``INAT_USERNAME``
    * ``INAT_PASSWORD``
    * ``INAT_APP_ID``
    * ``INAT_APP_SECRET``

    .. admonition:: Set environment variables in python:
        :class: toggle

        >>> import os
        >>> os.environ['INAT_USERNAME'] = 'my_username'
        >>> os.environ['INAT_PASSWORD'] = 'my_password'
        >>> os.environ['INAT_APP_ID'] = '33f27dc63bdf27f4ca6cd95dd9dcd5df'
        >>> os.environ['INAT_APP_SECRET'] = 'bbce628be722bfe2abd5fc566ba83de4'

    .. admonition:: Set environment variables in a POSIX shell (bash, etc.):
        :class: toggle

        .. code-block:: bash

            export INAT_USERNAME="my_username"
            export INAT_PASSWORD="my_password"
            export INAT_APP_ID="33f27dc63bdf27f4ca6cd95dd9dcd5df"
            export INAT_APP_SECRET="bbce628be722bfe2abd5fc566ba83de4"

    .. admonition:: Set environment variables in a Windows shell:
        :class: toggle

        .. code-block:: bat

            set INAT_USERNAME="my_username"
            set INAT_PASSWORD="my_password"
            set INAT_APP_ID="33f27dc63bdf27f4ca6cd95dd9dcd5df"
            set INAT_APP_SECRET="bbce628be722bfe2abd5fc566ba83de4"

    .. admonition:: Set environment variables in PowerShell:
        :class: toggle

        .. code-block:: powershell

            $Env:INAT_USERNAME="my_username"
            $Env:INAT_PASSWORD="my_password"
            $Env:INAT_APP_ID="33f27dc63bdf27f4ca6cd95dd9dcd5df"
            $Env:INAT_APP_SECRET="bbce628be722bfe2abd5fc566ba83de4"

    Examples:

        With keyword arguments:

        >>> access_token = get_access_token(
        >>>     username='my_username',
        >>>     password='my_password',
        >>>     app_id='33f27dc63bdf27f4ca6cd95dd9dcd5df',
        >>>     app_secret='bbce628be722bfe2abd5fc566ba83de4',
        >>> )

        With environment variables set:

        >>> access_token = get_access_token()

        If you would like to run custom requests for endpoints not yet implemented in pyinaturalist,
        you can authenticate these requests by putting the token in your HTTP headers as follows:

        >>> import requests
        >>> requests.get(
        >>>     'https://www.inaturalist.org/observations/1234',
        >>>      headers={'Authorization': f'Bearer {access_token}'},
        >>> )

    Args:
        username: iNaturalist username
        password: iNaturalist password
        app_id: iNaturalist application ID
        app_secret: iNaturalist application secret
        user_agent: a user-agent string that will be passed to iNaturalist.
    """
    payload = {
        "username": username or getenv("INAT_USERNAME"),
        "password": password or getenv("INAT_PASSWORD"),
        "client_id": app_id or getenv("INAT_APP_ID"),
        "client_secret": app_secret or getenv("INAT_APP_SECRET"),
        "grant_type": "password",
    }
    if not all(payload.values()):
        raise AuthenticationError("Not all authentication parameters were provided")

    response = post(
        f"{INAT_BASE_URL}/oauth/token",
        json=payload,
        user_agent=user_agent,
    )
    try:
        return response.json()["access_token"]
    except KeyError:
        raise AuthenticationError("Authentication error, please check credentials.")


@document_request_params(
    [
        docs._observation_common,
        docs._observation_rest_only,
        docs._bounding_box,
        docs._pagination,
    ]
)
def get_observations(user_agent: str = None, **kwargs) -> Union[List, str]:
    """Get observation data, optionally in an alternative format. Also see
    :py:func:`.get_geojson_observations` for GeoJSON format (not included here because it wraps
    a separate API endpoint).

    **API reference:** https://www.inaturalist.org/pages/api+reference#get-observations

    Example:

        >>> get_observations(id=45414404, format="atom")

        .. admonition:: Example Response (atom)
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations.atom
                :language: xml

        .. admonition:: Example Response (csv)
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations.csv

        .. admonition:: Example Response (dwc)
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations.dwc
                :language: xml

        .. admonition:: Example Response (json)
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations.json
                :language: json

        .. admonition:: Example Response (kml)
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations.kml
                :language: xml

        .. admonition:: Example Response (widget)
            :class: toggle

            .. literalinclude:: ../sample_data/get_observations.js
                :language: javascript

    Returns:
        Return type will be ``dict`` for the ``json`` response format, and ``str`` for all
        others.
    """
    response_format = kwargs.pop("response_format", "json")
    if response_format == "geojson":
        raise ValueError("For geojson format, use pyinaturalist.node_api.get_geojson_observations")
    if response_format not in OBSERVATION_FORMATS:
        raise ValueError("Invalid response format")
    validate_multiple_choice_param(kwargs, "order_by", REST_OBS_ORDER_BY_PROPERTIES)

    response = get(
        f"{INAT_BASE_URL}/observations.{response_format}",
        params=kwargs,
        user_agent=user_agent,
    )

    if response_format == "json":
        return convert_lat_long_to_float(response.json())
    else:
        return response.text


@document_request_params([docs._search_query, docs._page])
def get_observation_fields(user_agent: str = None, **kwargs) -> ListResponse:
    """Search observation fields. Observation fields are basically typed data fields that
    users can attach to observation.

    **API reference:** https://www.inaturalist.org/pages/api+reference#get-observation_fields

    Example:

        >>> get_observation_fields(q='number of individuals')
        >>> # Show just observation field IDs and names
        >>> from pprint import pprint
        >>> pprint({r['id']: r['name'] for r in response})

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_observation_fields_page1.json
                :language: javascript

    Returns:
        Observation fields as a list of dicts
    """
    kwargs = check_deprecated_params(**kwargs)
    response = get(
        f"{INAT_BASE_URL}/observation_fields.json",
        params=kwargs,
        user_agent=user_agent,
    )
    return response.json()


@document_request_params([docs._search_query])
def get_all_observation_fields(**kwargs) -> ListResponse:
    """
    Like :py:func:`.get_observation_fields()`, but handles pagination for you.

    Example:

        >>> get_all_observation_fields(q='number of')

    Returns:
        Observation fields as a list of dicts. Response format is the same as the inner
        "results" object returned by :py:func:`.get_observation_fields`.
    """
    results = []  # type: List[Dict[str, Any]]
    page = 1

    while True:
        r = get_observation_fields(page=page, **kwargs)

        if not r:
            return results

        results += r
        page += 1
        sleep(THROTTLING_DELAY)


def put_observation_field_values(
    observation_id: int,
    observation_field_id: int,
    value: Any,
    access_token: str,
    user_agent: str = None,
) -> JsonResponse:
    # TODO: Also implement a put_or_update_observation_field_values() that deletes then recreates the field_value?
    # TODO: Return some meaningful exception if it fails because the field is already set.
    # TODO: It appears pushing the same value/pair twice in a row (but deleting it meanwhile via the UI)...
    # TODO: ...triggers an error 404 the second time (report to iNaturalist?)
    """Set an observation field (value) on an observation.
    Will fail if this observation field is already set for this observation.

    To find an `observation_field_id`, either user :py:func:`.get_observation_fields` or search
    on iNaturalist: https://www.inaturalist.org/observation_fields

    **API reference:** https://www.inaturalist.org/pages/api+reference#put-observation_field_values-id

    Example:
            >>> # First find an observation field by name, if the ID is unknown
            >>> response = get_observation_fields('vespawatch_id')
            >>> observation_field_id = response[0]['id']
            >>>
            >>> put_observation_field_values(
            >>>     observation_id=7345179,
            >>>     observation_field_id=observation_field_id,
            >>>     value=250,
            >>>     access_token=token,
            >>> )

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/put_observation_field_value_result.json
                :language: javascript

    Args:
        observation_id: ID of the observation receiving this observation field value
        observation_field_id: ID of the observation field for this observation field value
        value: Value for the observation field
        access_token: access_token: The access token, as returned by :func:`get_access_token()`
        user_agent: A user-agent string that will be passed to iNaturalist.

    Returns:
        The nwely updated field value record
    """

    payload = {
        "observation_field_value": {
            "observation_id": observation_id,
            "observation_field_id": observation_field_id,
            "value": value,
        }
    }

    response = put(
        f"{INAT_BASE_URL}/observation_field_values/{observation_field_id}",
        access_token=access_token,
        user_agent=user_agent,
        json=payload,
    )

    response.raise_for_status()
    return response.json()


def create_observations(params: RequestParams = None, **kwargs):
    """Create a new observation.
    Note: Creating multiple observations sould be possible according to the docs, but it does not
    appear to work.
    """
    warn(
        "create_observations() has been deprecated, as creating multiple observations is not "
        "currently functional. Please use create_observation() instead."
    )
    create_observation(params, **kwargs)


# TODO: more thorough usage example
@document_request_params([docs._legacy_params, docs._access_token, docs._create_observation])
def create_observation(
    params: RequestParams = None, access_token: str = None, user_agent: str = None, **kwargs
) -> ListResponse:
    """Create a new observation.

    **API reference:** https://www.inaturalist.org/pages/api+reference#post-observations

    Example:
        >>> token = get_access_token('...')
        >>> create_observation(
        >>>     access_token=token,
        >>>     species_guess='Pieris rapae',
        >>>     local_photos='~/observation_photos/2020_09_01_14003156.jpg',
        >>>     observation_fields={297: 1},  # 297 is the obs. field ID for 'Number of individuals'
        >>> )

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/create_observation_result.json
                :language: javascript

        .. admonition:: Example Response (failure)
            :class: toggle

            .. literalinclude:: ../sample_data/create_observation_fail.json
                :language: javascript

    Returns:
        JSON response containing the newly created observation(s)

    Raises:
        :py:exc:`requests.HTTPError`, if the call is not successful. iNaturalist returns an
        error 422 (unprocessable entity) if it rejects the observation data (for example an
        observation date in the future or a latitude > 90. In that case the exception's
        ``response`` attribute gives more details about the errors.
    """
    # Accept either top-level params (like most other endpoints)
    # or nested {"observation": params} (like the iNat API accepts directly)
    if "observation" in kwargs:
        kwargs.update(kwargs.pop("observation"))
    kwargs = check_deprecated_params(params, **kwargs)
    kwargs = convert_observation_fields(kwargs)
    if "local_photos" in kwargs:
        kwargs["local_photos"] = ensure_file_objs(kwargs["local_photos"])

    response = post(
        url=f"{INAT_BASE_URL}/observations.json",
        json={"observation": kwargs},
        access_token=access_token,
        user_agent=user_agent,
    )
    response.raise_for_status()
    return response.json()


@document_request_params(
    [
        docs._observation_id,
        docs._legacy_params,
        docs._access_token,
        docs._create_observation,
        docs._update_observation,
    ]
)
def update_observation(
    observation_id: int,
    params: RequestParams = None,
    access_token: str = None,
    user_agent: str = None,
    **kwargs,
) -> ListResponse:
    """
    Update a single observation.

    **API reference:** https://www.inaturalist.org/pages/api+reference#put-observations-id

    .. note::

        Unlike the underlying REST API endpoint, this function will **not** delete any existing
        photos from your observation if not specified in ``local_photos``. If you want this to
        behave the same as the REST API and you do want to delete photos, call with
        ``ignore_photos=False``.

    Example:

        >>> token = get_access_token('...')
        >>> update_observation(
        >>>     17932425,
        >>>     access_token=token,
        >>>     description="updated description!",
        >>> )

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/update_observation_result.json
                :language: javascript

    Returns:
        JSON response containing the newly updated observation(s)

    Raises:
        :py:exc:`requests.HTTPError`, if the call is not successful. iNaturalist returns an
            error 410 if the observation doesn't exists or belongs to another user.
    """
    # Accept either top-level params (like most other endpoints)
    # or nested params (like the iNat API actually accepts)
    if "observation" in kwargs:
        kwargs.update(kwargs.pop("observation"))
    kwargs = check_deprecated_params(params, **kwargs)
    kwargs = convert_observation_fields(kwargs)
    if "local_photos" in kwargs:
        kwargs["local_photos"] = ensure_file_objs(kwargs["local_photos"])

    # This is the one Boolean parameter that's specified as an int, for some reason.
    # Also, set it to True if not specified, which seems like much saner default behavior.
    if "ignore_photos" in kwargs:
        kwargs["ignore_photos"] = int(kwargs["ignore_photos"])
    else:
        kwargs["ignore_photos"] = 1

    response = put(
        url=f"{INAT_BASE_URL}/observations/{observation_id}.json",
        json={"observation": kwargs},
        access_token=access_token,
        user_agent=user_agent,
    )
    response.raise_for_status()
    return response.json()


def add_photo_to_observation(
    observation_id: int,
    photo: FileOrPath,
    access_token: str,
    user_agent: str = None,
):
    """Upload a local photo and assign it to an existing observation.

    **API reference:** https://www.inaturalist.org/pages/api+reference#post-observation_photos

    Example:

        >>> token = get_access_token('...')
        >>> add_photo_to_observation(
        >>>     1234,
        >>>     '~/observation_photos/2020_09_01_14003156.jpg',
        >>>     access_token=token,
        >>> )

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/add_photo_to_observation.json
                :language: javascript

    Args:
        observation_id: the ID of the observation
        photo: An image file, file-like object, or path
        access_token: the access token, as returned by :func:`get_access_token()`
        user_agent: a user-agent string that will be passed to iNaturalist.

    Returns:
        Information about the newly created photo
    """
    response = post(
        url=f"{INAT_BASE_URL}/observation_photos",
        access_token=access_token,
        data={"observation_photo[observation_id]": observation_id},
        files={"file": ensure_file_obj(photo)},
        user_agent=user_agent,
    )

    return response.json()


@document_request_params([docs._observation_id, docs._access_token])
def delete_observation(observation_id: int, access_token: str = None, user_agent: str = None):
    """
    Delete an observation.

    **API reference:** https://www.inaturalist.org/pages/api+reference#delete-observations-id

    Example:

        >>> token = get_access_token('...')
        >>> delete_observation(17932425, token)

    Returns:
        If successful, no response is returned from this endpoint

    Raises:
        :py:exc:`.ObservationNotFound` if the requested observation doesn't exist
        :py:exc:`requests.HTTPError` (403) if the observation belongs to another user
    """
    response = delete(
        url=f"{INAT_BASE_URL}/observations/{observation_id}.json",
        access_token=access_token,
        user_agent=user_agent,
        headers={"Content-type": "application/json"},
    )
    if response.status_code == 404:
        raise ObservationNotFound
    response.raise_for_status()
