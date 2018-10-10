# Code used to access the (read/write, but slow) Rails based API of iNaturalist
# See: https://www.inaturalist.org/pages/api+reference
from time import sleep

import requests

from inaturalist.constants import THROTTLING_DELAY, INAT_BASE_URL


class AuthenticationError(Exception):
    pass


def get_observation_fields(search_query="", page=1):
    """
    Search the (globally available) observation
    :param search_query:
    :param page:
    :return:
    """
    payload = {
        'q': search_query,
        'page': page
    }

    response = requests.get("{base_url}/observation_fields.json".format(base_url=INAT_BASE_URL), params=payload)
    return response.json()


def get_all_observation_fields(search_query=""):
    """ Like get_observation_fields(), but handles pagination for you. """
    results = []
    page = 1

    while True:
        r = get_observation_fields(search_query=search_query, page=page)

        if not r:
            return results

        results = results + r
        page = page + 1
        sleep(THROTTLING_DELAY)


def put_observation_field_values(observation_id, observation_field_id, value, access_token):
    # TODO: Also implement a put_or_update_observation_field_values() that deletes the property first, if it already exists?
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

    response = requests.put("{base_url}/observation_field_values/{id}".format(base_url=INAT_BASE_URL, id=observation_field_id),
                            headers=_build_auth_header(access_token),
                            json=payload)
    # TODO: Return some meaningful exception if it fails because the field is already set.
    return response


def get_access_token(username, password, app_id, app_secret):
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


def _build_auth_header(access_token):
    return {"Authorization": "Bearer %s" % access_token}


def add_photo_to_observation(observation_id, file_object, access_token):
    """Upload a picture and assign it to an existing observation.

    :param observation_id: the ID of the observation
    :param file_object: a file like object of the picture. Example: file_object = open('/Users/nicolasnoe/vespa.jpg', 'rb')
    :param access_token: the access token, as returned by `get_access_token()`
    """
    data = {'observation_photo[observation_id]': observation_id}
    file_data = {'file': file_object}

    response = requests.post(url="{base_url}/observation_photos".format(base_url=INAT_BASE_URL),
                             headers=_build_auth_header(access_token),
                             data=data,
                             files=file_data)

    return response.json()

def create_observations(params, access_token):
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