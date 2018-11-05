# Code used to access the (read/write, but slow) Rails based API of iNaturalist
# See: https://www.inaturalist.org/pages/api+reference
from time import sleep
from typing import Dict, Any, List, BinaryIO, Union  # noqa: F401

import requests

from pyinaturalist.constants import THROTTLING_DELAY, INAT_BASE_URL
from pyinaturalist.exceptions import AuthenticationError


def get_observation_fields(search_query: str="", page: int=1):
    """
    Search the (globally available) observation
    :param search_query:
    :param page:
    :return:
    """
    payload = {
        'q': search_query,
        'page': page
    }  # type: Dict[str, Union[int, str]]

    response = requests.get("{base_url}/observation_fields.json".format(base_url=INAT_BASE_URL), params=payload)
    return response.json()


def get_all_observation_fields(search_query: str="") -> List[Dict[str, Any]]:
    """
    Like get_observation_fields(), but handles pagination for you.

    :param search_query: a string to search
    """
    results = []  # type: List[Dict[str, Any]]
    page = 1

    while True:
        r = get_observation_fields(search_query=search_query, page=page)

        if not r:
            return results

        results = results + r
        page = page + 1
        sleep(THROTTLING_DELAY)


def put_observation_field_values(observation_id: int, observation_field_id: int, value: Any, access_token: str):
    # TODO: Also implement a put_or_update_observation_field_values() that deletes then recreates the field_value?
    """Sets an observation field value.

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
                            headers=_build_auth_header(access_token),
                            json=payload)
    # TODO: Return some meaningful exception if it fails because the field is already set.
    return response


def get_access_token(username: str, password: str, app_id: str, app_secret: str) -> str:
    """
    Get an access token using the user's iNaturalist username and password.

    (you still need an iNaturalist app to do this)

    :param username:
    :param password:
    :param app_id:
    :param app_secret:
    :return: the access token, example use: headers = {"Authorization": "Bearer %s" % access_token}
    """
    payload = {
        'client_id': app_id,
        'client_secret': app_secret,
        'grant_type': "password",
        'username': username,
        'password': password
    }

    response = requests.post("{base_url}/oauth/token".format(base_url=INAT_BASE_URL), payload)
    try:
        return response.json()["access_token"]
    except KeyError:
        raise AuthenticationError("Authentication error, please check credentials.")


def _build_auth_header(access_token: str) -> Dict[str, str]:
    return {"Authorization": "Bearer %s" % access_token}


def add_photo_to_observation(observation_id: int, file_object: BinaryIO, access_token: str):
    """Upload a picture and assign it to an existing observation.

    :param observation_id: the ID of the observation
    :param file_object: a file-like object for the picture. Example: open('/Users/nicolasnoe/vespa.jpg', 'rb')
    :param access_token: the access token, as returned by `get_access_token()`
    """
    data = {'observation_photo[observation_id]': observation_id}
    file_data = {'file': file_object}

    response = requests.post(url="{base_url}/observation_photos".format(base_url=INAT_BASE_URL),
                             headers=_build_auth_header(access_token),
                             data=data,
                             files=file_data)

    return response.json()


def create_observations(params: Dict[str, Dict[str, Any]], access_token: str) -> List[Dict[str, Any]]:
    """Create a single or several (if passed an array) observations).

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
                             headers=_build_auth_header(access_token))
    return response.json()


def update_observation(observation_id: int, params: Dict[str, Any], access_token: str) -> List[Dict[str, Any]]:
    """
    Update a single observation. See https://www.inaturalist.org/pages/api+reference#put-observations-id

    :param observation_id: the ID of the observation to update
    :param params: to be passed to iNaturalist API
    :param access_token: the access token, as returned by :func:`get_access_token()`
    :return: iNaturalist's JSON response, as a Python object
    :raise: requests.HTTPError, if the call is not successful. iNaturalist returns an error 410 if the observation
    doesn't exists or belongs to another user (as of November 2018).
    """

    response = requests.put(url="{base_url}/observations/{id}.json".format(base_url=INAT_BASE_URL, id=observation_id),
                            json=params,
                            headers=_build_auth_header(access_token))

    response.raise_for_status()
    return response.json()
