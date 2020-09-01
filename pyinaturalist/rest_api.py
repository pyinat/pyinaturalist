"""
Code used to access the (read/write, but slow) Rails based API of iNaturalist
See: https://www.inaturalist.org/pages/api+reference
"""
from json import JSONDecodeError
from time import sleep
from typing import Dict, Any, List, BinaryIO, Union

from urllib.parse import urljoin

from pyinaturalist.api_docs import (
    document_request_params,
    get_observations_params_rest as get_observations_params,
    get_observation_fields_params,
    get_all_observation_fields_params,
    create_observations_params,
    update_observation_params,
    delete_observation_params,
)
from pyinaturalist.constants import OBSERVATION_FORMATS, THROTTLING_DELAY, INAT_BASE_URL
from pyinaturalist.exceptions import AuthenticationError, ObservationNotFound
from pyinaturalist.api_requests import delete, get, post, put
from pyinaturalist.request_params import check_deprecated_params
from pyinaturalist.response_format import convert_lat_long_to_float


@document_request_params(get_observations_params)
def get_observations(user_agent: str = None, **params) -> Union[List, str]:
    """Get observation data, optionally in an alternative format. Also see
    :py:func:`.get_geojson_observations` for GeoJSON format (not included here because it wraps
    a separate API endpoint).

    For API parameters, see: https://www.inaturalist.org/pages/api+reference#get-observations

    Example::

        get_observations(id=45414404, format="dwc")

    Returns:
        Return type will be ``dict`` for the ``json`` response format, and ``str`` for all
        others.
    """
    response_format = params.get("response_format", "json")
    if response_format == "geojson":
        raise ValueError("For geojson format, use pyinaturalist.node_api.get_geojson_observations")
    if response_format not in OBSERVATION_FORMATS:
        raise ValueError("Invalid response format")

    response = get(
        urljoin(INAT_BASE_URL, "observations.{}".format(response_format)),
        params=params,
        user_agent=user_agent,
    )

    if response_format == "json":
        return convert_lat_long_to_float(response.json())
    else:
        return response.text


@document_request_params(get_observation_fields_params)
def get_observation_fields(user_agent: str = None, **kwargs) -> List[Dict[str, Any]]:
    """Search observation fields. Observation fields are basically typed data fields that
    users can attach to observation.
    API reference: https://www.inaturalist.org/pages/api+reference#get-observation_fields

    Returns:
        Observation fields as a list of dicts
    """
    kwargs = check_deprecated_params(kwargs)
    response = get(
        "{base_url}/observation_fields.json".format(base_url=INAT_BASE_URL),
        params=kwargs,
        user_agent=user_agent,
    )
    return response.json()


@document_request_params(get_all_observation_fields_params)
def get_all_observation_fields(**kwargs) -> List[Dict[str, Any]]:
    """
    Like :py:func:`.get_observation_fields()`, but handles pagination for you.

    Returns:
        Observation fields as a list of dicts
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
) -> Dict[str, Any]:
    # TODO: Also implement a put_or_update_observation_field_values() that deletes then recreates the field_value?
    # TODO: Write example use in docstring.
    # TODO: Return some meaningful exception if it fails because the field is already set.
    # TODO: Also show in example  to obtain the observation_field_id?
    # TODO: What happens when parameters are invalid
    # TODO: It appears pushing the same value/pair twice in a row (but deleting it meanwhile via the UI)...
    # TODO: ...triggers an error 404 the second time (report to iNaturalist?)
    """Set an observation field (value) on an observation.
    Will fail if this observation_field is already set for this observation.

    Example:
            >>> put_observation_field_values(
            >>>     observation_id=7345179,
            >>>     observation_field_id=9613,
            >>>     value=250,
            >>>     access_token=token,
            >>> )
            {'id': 31,
             'observation_id': 18166477,
             'observation_field_id': 31,
             'value': 'fouraging',
             'created_at': '2012-09-29T11:05:44.935+02:00',
             'updated_at': '2018-11-13T10:49:47.985+01:00',
             'user_id': 1,
             'updater_id': 1263313,
             'uuid': 'b404b654-1bf0-4299-9288-52eeda7ac0db',
             'created_at_utc': '2012-09-29T09:05:44.935Z',
             'updated_at_utc': '2018-11-13T09:49:47.985Z'}

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
        "{base_url}/observation_field_values/{id}".format(
            base_url=INAT_BASE_URL, id=observation_field_id
        ),
        access_token=access_token,
        user_agent=user_agent,
        json=payload,
    )

    response.raise_for_status()
    return response.json()


def get_access_token(
    username: str, password: str, app_id: str, app_secret: str, user_agent: str = None
) -> str:
    """Get an access token using the user's iNaturalist username and password.
    You still need an iNaturalist app to do this.

    Example:
        >>> access_token = get_access_token('...')
        >>> headers = {"Authorization": f"Bearer {access_token}"}

    Args:
        username: iNaturalist username
        password: iNaturalist password
        app_id: iNaturalist application ID
        app_secret: iNaturalist application secret
        user_agent: a user-agent string that will be passed to iNaturalist.
    """
    payload = {
        "client_id": app_id,
        "client_secret": app_secret,
        "grant_type": "password",
        "username": username,
        "password": password,
    }

    response = post(
        "{base_url}/oauth/token".format(base_url=INAT_BASE_URL),
        json=payload,
        user_agent=user_agent,
    )
    try:
        return response.json()["access_token"]
    except KeyError:
        raise AuthenticationError("Authentication error, please check credentials.")


def add_photo_to_observation(
    observation_id: int,
    file_object: BinaryIO,
    access_token: str,
    user_agent: str = None,
):
    """Upload a picture and assign it to an existing observation.

    Args:
        observation_id: the ID of the observation
        file_object: a file-like object for the picture. Example: open('/Users/nicolasnoe/vespa.jpg', 'rb')
        access_token: the access token, as returned by :func:`get_access_token()`
        user_agent: a user-agent string that will be passed to iNaturalist.
    """
    data = {"observation_photo[observation_id]": observation_id}
    file_data = {"file": file_object}

    response = post(
        url="{base_url}/observation_photos".format(base_url=INAT_BASE_URL),
        access_token=access_token,
        user_agent=user_agent,
        data=data,
        files=file_data,
    )

    return response.json()


# TODO: Implement `observation_field_values_attributes`, and simplify nested data structures
# TODO: implement `local_photos` and allow simply passing local file path(s)
@document_request_params(create_observations_params)
def create_observations(
    params: Dict[str, Dict[str, Any]], access_token: str, user_agent: str = None, **kwargs
) -> List[Dict[str, Any]]:
    """Create one or more observations.
    For API reference, see: https://www.inaturalist.org/pages/api+reference#post-observations

    Example:
        >>> params = {'observation': {'species_guess': 'Pieris rapae'}}
        >>> token = get_access_token('...')
        >>> create_observations(params=params, access_token=token)

    Returns:
         The newly created observation(s) in JSON format

    Raises:
        :py:exc:`requests.HTTPError`, if the call is not successful. iNaturalist returns an
        error 422 (unprocessable entity) if it rejects the observation data (for example an
        observation date in the future or a latitude > 90. In that case the exception's
        `response` attribute give details about the errors.

    TODO investigate: according to the doc, we should be able to pass multiple observations (in an array, and in
    renaming observation to observations, but as far as I saw they are not created (while a status of 200 is returned)
    """
    # This is the one Boolean parameter that's specified as an int, for some reason
    if "ignore_photos" in kwargs:
        kwargs["ignore_photos"] = int(kwargs["ignore_photos"])

    response = post(
        url="{base_url}/observations.json".format(base_url=INAT_BASE_URL),
        json=params,
        access_token=access_token,
        user_agent=user_agent,
    )
    response.raise_for_status()
    return response.json()


@document_request_params(update_observation_params)
def update_observation(
    observation_id: int, params: Dict[str, Any], access_token: str, user_agent: str = None, **kwargs
) -> List[Dict[str, Any]]:
    """
    Update a single observation. See https://www.inaturalist.org/pages/api+reference#put-observations-id

    Returns:
        iNaturalist's JSON response, as a Python object

    Raises:
        :py:exc:`requests.HTTPError`, if the call is not successful. iNaturalist returns an
            error 410 if the observation doesn't exists or belongs to another user.
    """
    if "ignore_photos" in kwargs:
        kwargs["ignore_photos"] = int(kwargs["ignore_photos"])

    response = put(
        url="{base_url}/observations/{id}.json".format(base_url=INAT_BASE_URL, id=observation_id),
        json=params,
        access_token=access_token,
        user_agent=user_agent,
    )
    response.raise_for_status()
    return response.json()


# TODO: test this (success case, wrong_user/403 case)
# TODO: document example in readme
@document_request_params(delete_observation_params)
def delete_observation(observation_id: int, access_token: str = None, user_agent: str = None):
    """
    Delete an observation.

    Returns:
        If successful, no response is returned from this endpoint

    Raises:
        :py:exc:`.ObservationNotFound` if the requested observation doesn't exist
        :py:exc:`requests.HTTPError` (403) if the observation belongs to another user
    """
    response = delete(
        url="{base_url}/observations/{id}.json".format(base_url=INAT_BASE_URL, id=observation_id),
        access_token=access_token,
        user_agent=user_agent,
        headers={"Content-type": "application/json"},
    )
    if response.status_code == 404:
        raise ObservationNotFound
    response.raise_for_status()
