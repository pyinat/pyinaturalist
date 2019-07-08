# Code used to access the (read/write, but slow) Rails based API of iNaturalist
# See: https://www.inaturalist.org/pages/api+reference
from time import sleep
from typing import Dict, Any, List, BinaryIO, Union  # noqa: F401

import requests

from pyinaturalist.constants import THROTTLING_DELAY, INAT_BASE_URL
from pyinaturalist.exceptions import AuthenticationError, ObservationNotFound
from pyinaturalist.helpers import get_user_agent


def _build_headers(access_token: str = None, user_agent: str = None) -> Dict[str, str]:
    headers = {'User-Agent': get_user_agent(user_agent)}

    if access_token:
        headers['Authorization'] = 'Bearer %s' % access_token

    return headers


def get_observation_fields(search_query: str = "", page: int = 1, user_agent: str = None) -> List[Dict[str, Any]]:
    """
    Search the (globally available) observation

    :param search_query:
    :param page:
    :param user_agent: a user-agent (string) passed to iNaturalist in order to identify your project or application. \
    If not set, 'Pyinaturalist <VERSION>' will be used.

    :return:
    """
    payload = {
        'q': search_query,
        'page': page
    }  # type: Dict[str, Union[int, str]]

    response = requests.get("{base_url}/observation_fields.json".format(base_url=INAT_BASE_URL), params=payload,
                            headers=_build_headers(user_agent=user_agent))
    return response.json()


def get_all_observation_fields(search_query: str = "", user_agent: str = None) -> List[Dict[str, Any]]:
    """
    Like get_observation_fields(), but handles pagination for you.

    :param search_query: a string to search
    :param user_agent: a user-agent (string) passed to iNaturalist in order to identify your project or application. \
    If not set, 'Pyinaturalist <VERSION>' will be used.
    """
    results = []  # type: List[Dict[str, Any]]
    page = 1

    while True:
        r = get_observation_fields(search_query=search_query, page=page, user_agent=user_agent)

        if not r:
            return results

        results = results + r
        page = page + 1
        sleep(THROTTLING_DELAY)


def put_observation_field_values(observation_id: int, observation_field_id: int, value: Any,
                                 access_token: str, user_agent: str = None) -> Dict[str, Any]:
    # TODO: Also implement a put_or_update_observation_field_values() that deletes then recreates the field_value?
    # TODO: Write example use in docstring.
    # TODO: Return some meaningful exception if it fails because the field is already set.
    # TODO: Also show in example  to obtain the observation_field_id?
    # TODO: What happens when parameters are invalid
    # TODO: It appears pushing the same value/pair twice in a row (but deleting it meanwhile via the UI)...
    # TODO: ...triggers an error 404 the second time (report to iNaturalist?)
    """Sets an observation field (value) on an observation.

    :param observation_id:
    :param observation_field_id:
    :param value:
    :param access_token: access_token: the access token, as returned by :func:`get_access_token()`
    :param user_agent: a user-agent (string) passed to iNaturalist in order to identify your project or application. \
    If not set, 'Pyinaturalist <VERSION>' will be used.

    :returns: iNaturalist's response as a dict, for example:
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

    Will fail if this observation_field is already set for this observation.
    """

    payload = {
        'observation_field_value': {
            'observation_id': observation_id,
            'observation_field_id': observation_field_id,
            'value': value
        }
    }

    response = requests.put("{base_url}/observation_field_values/{id}".format(base_url=INAT_BASE_URL,
                                                                              id=observation_field_id),
                            headers=_build_headers(access_token=access_token, user_agent=user_agent),
                            json=payload)

    response.raise_for_status()
    return response.json()


def get_access_token(username: str, password: str, app_id: str, app_secret: str, user_agent: str = None) -> str:
    """
    Get an access token using the user's iNaturalist username and password.

    (you still need an iNaturalist app to do this)

    :param username:
    :param password:
    :param app_id:
    :param app_secret:
    :param user_agent: a user-agent (string) passed to iNaturalist in order to identify your project or application. \
    If not set, 'Pyinaturalist <VERSION>' will be used.

    :return: the access token, example use: headers = {"Authorization": "Bearer %s" % access_token}
    """
    payload = {
        'client_id': app_id,
        'client_secret': app_secret,
        'grant_type': "password",
        'username': username,
        'password': password
    }

    response = requests.post("{base_url}/oauth/token".format(base_url=INAT_BASE_URL),
                             payload,
                             headers=_build_headers(user_agent=user_agent))
    try:
        return response.json()["access_token"]
    except KeyError:
        raise AuthenticationError("Authentication error, please check credentials.")


def add_photo_to_observation(observation_id: int, file_object: BinaryIO, access_token: str, user_agent: str = None):
    """Upload a picture and assign it to an existing observation.

    :param observation_id: the ID of the observation
    :param file_object: a file-like object for the picture. Example: open('/Users/nicolasnoe/vespa.jpg', 'rb')
    :param access_token: the access token, as returned by :func:`get_access_token()`
    :param user_agent: a user-agent (string) passed to iNaturalist in order to identify your project or application. \
    If not set, 'Pyinaturalist <VERSION>' will be used.
    """
    data = {'observation_photo[observation_id]': observation_id}
    file_data = {'file': file_object}

    response = requests.post(url="{base_url}/observation_photos".format(base_url=INAT_BASE_URL),
                             headers=_build_headers(access_token=access_token, user_agent=user_agent),
                             data=data,
                             files=file_data)

    return response.json()


def create_observations(params: Dict[str, Dict[str, Any]],
                        access_token: str, user_agent: str = None) -> List[Dict[str, Any]]:
    """Create a single or several (if passed an array) observations).

    :param params:
    :param access_token: the access token, as returned by :func:`get_access_token()`
    :param user_agent: a user-agent (string) passed to iNaturalist in order to identify your project or application. \
    If not set, 'Pyinaturalist <VERSION>' will be used.

    :return: iNaturalist's JSON response, as a Python object
    :raise: requests.HTTPError, if the call is not successful. iNaturalist returns an error 422 (unprocessable entity)
            if it rejects the observation data (for example an observation date in the future or a latitude > 90. In
            that case the exception's `response` attribute give details about the errors.

    allowed params: see https://www.inaturalist.org/pages/api+reference#post-observations

    Example:

        params = {'observation':
            {'species_guess': 'Pieris rapae'},
        }

    TODO investigate: according to the doc, we should be able to pass multiple observations (in an array, and in
    renaming observation to observations, but as far as I saw they are not created (while a status of 200 is returned)
    """
    response = requests.post(url="{base_url}/observations.json".format(base_url=INAT_BASE_URL),
                             json=params,
                             headers=_build_headers(access_token=access_token, user_agent=user_agent))
    response.raise_for_status()
    return response.json()


def update_observation(observation_id: int, params: Dict[str, Any],
                       access_token: str, user_agent: str = None) -> List[Dict[str, Any]]:
    """
    Update a single observation. See https://www.inaturalist.org/pages/api+reference#put-observations-id

    :param observation_id: the ID of the observation to update
    :param params: to be passed to iNaturalist API
    :param access_token: the access token, as returned by :func:`get_access_token()`
    :param user_agent: a user-agent (string) passed to iNaturalist in order to identify your project or application. \
    If not set, 'Pyinaturalist <VERSION>' will be used.

    :return: iNaturalist's JSON response, as a Python object
    :raise: requests.HTTPError, if the call is not successful. iNaturalist returns an error 410 if the observation
            doesn't exists or belongs to another user (as of November 2018).
    """

    response = requests.put(url="{base_url}/observations/{id}.json".format(base_url=INAT_BASE_URL, id=observation_id),
                            json=params,
                            headers=_build_headers(access_token=access_token, user_agent=user_agent))
    response.raise_for_status()
    return response.json()


# TODO: test this (success case, wrong_user/403 case)
# TODO: document example in readme
def delete_observation(observation_id: int, access_token: str, user_agent: str = None) -> List[Dict[str, Any]]:
    """
    Delete an observation.

    :param observation_id:
    :param access_token:
    :param user_agent: a user-agent (string) passed to iNaturalist in order to identify your project or application. \
    If not set, 'Pyinaturalist <VERSION>' will be used.

    :return: iNaturalist's JSON response, as a Python object (currently raise a JSONDecodeError because of an
             iNaturalist bug
    :raise: ObservationNotFound if the requested observation doesn't exists, requests.HTTPError (403) if the
            observation belongs to another user
    """

    headers = _build_headers(access_token=access_token, user_agent=user_agent)
    headers['Content-type'] = 'application/json'

    response = requests.delete(url="{base_url}/observations/{id}.json".format(base_url=INAT_BASE_URL,
                                                                              id=observation_id),
                               headers=headers)
    if response.status_code == 404:
        raise ObservationNotFound

    response.raise_for_status()
    # According to iNaturalist documentation, proper JSON should be returned. It seems however that the response is
    # currently empty (while the requests succeed), so you may receive a JSONDecode exception.
    # It has been reported to the iNaturalist team because the issue persists month after:
    # https://github.com/inaturalist/inaturalist/issues/2252
    return response.json()
