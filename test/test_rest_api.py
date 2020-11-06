from datetime import datetime, timedelta
from io import BytesIO
from unittest.mock import patch

import pytest
from requests import HTTPError

from pyinaturalist.constants import INAT_BASE_URL
from pyinaturalist.rest_api import (
    OBSERVATION_FORMATS,
    get_all_observation_fields,
    get_observations,
    get_observation_fields,
    put_observation_field_values,
    create_observation,
    update_observation,
    add_photo_to_observation,
    delete_observation,
)
from pyinaturalist.exceptions import ObservationNotFound
from test.conftest import load_sample_data

PAGE_1_JSON_RESPONSE = load_sample_data("get_observation_fields_page1.json")
PAGE_2_JSON_RESPONSE = load_sample_data("get_observation_fields_page2.json")


def get_observations_response(response_format):
    response_format = response_format.replace("widget", "js")
    return load_sample_data(f"get_observations.{response_format}")


@pytest.mark.parametrize("response_format", OBSERVATION_FORMATS)
def test_get_observations(response_format, requests_mock):
    """ Test all supported observation data formats """
    response = get_observations_response(response_format)
    key = "json" if response_format == "json" else "text"

    requests_mock.get(
        f"{INAT_BASE_URL}/observations.{response_format}",
        status_code=200,
        **{key: response},
    )

    observations = get_observations(taxon_id=493595, response_format=response_format)

    # Ensure coordinate strings were converted to floats, for JSON format only
    if response_format == "json":
        response[0]["latitude"] = 50.646894
        response[0]["longitude"] = 4.360086
    assert observations == response


@pytest.mark.parametrize("response_format", ["geojson", "yaml"])
def test_get_observations__invalid_format(response_format):
    with pytest.raises(ValueError):
        get_observations(taxon_id=493595, response_format=response_format)


def test_get_observation_fields(requests_mock):
    """ get_observation_fields() work as expected (basic use)"""

    requests_mock.get(
        f"{INAT_BASE_URL}/observation_fields.json?q=sex&page=2",
        json=PAGE_2_JSON_RESPONSE,
        status_code=200,
    )

    obs_fields = get_observation_fields(q="sex", page=2)
    assert obs_fields == PAGE_2_JSON_RESPONSE


def test_get_all_observation_fields(requests_mock):
    """get_all_observation_fields() is able to paginate, accepts a search query and return correct results"""

    requests_mock.get(
        f"{INAT_BASE_URL}/observation_fields.json?q=sex&page=1",
        json=PAGE_1_JSON_RESPONSE,
        status_code=200,
    )

    requests_mock.get(
        f"{INAT_BASE_URL}/observation_fields.json?q=sex&page=2",
        json=PAGE_2_JSON_RESPONSE,
        status_code=200,
    )

    page_3_json_response = []
    requests_mock.get(
        f"{INAT_BASE_URL}/observation_fields.json?q=sex&page=3",
        json=page_3_json_response,
        status_code=200,
    )

    all_fields = get_all_observation_fields(q="sex")
    assert all_fields == PAGE_1_JSON_RESPONSE + PAGE_2_JSON_RESPONSE


def test_get_all_observation_fields_noparam(requests_mock):
    """get_all_observation_fields() can also be called without a search query without errors"""
    requests_mock.get(
        f"{INAT_BASE_URL}/observation_fields.json?page=1",
        json=[],
        status_code=200,
    )

    get_all_observation_fields()


def test_put_observation_field_values(requests_mock):
    requests_mock.put(
        f"{INAT_BASE_URL}/observation_field_values/31",
        json=load_sample_data("put_observation_field_value_result.json"),
        status_code=200,
    )

    r = put_observation_field_values(
        observation_id=18166477,
        observation_field_id=31,  # Animal behavior
        value="fouraging",
        access_token="valid token",
    )

    assert r["id"] == 31
    assert r["observation_field_id"] == 31
    assert r["observation_id"] == 18166477
    assert r["value"] == "fouraging"


def test_update_observation(requests_mock):
    requests_mock.put(
        f"{INAT_BASE_URL}/observations/17932425.json",
        json=load_sample_data("update_observation_result.json"),
        status_code=200,
    )

    params = {
        "ignore_photos": 1,
        "description": "updated description v2 !",
    }
    r = update_observation(17932425, access_token="valid token", **params)

    # If all goes well we got a single element representing the updated observation, enclosed in a list.
    assert len(r) == 1
    assert r[0]["id"] == 17932425
    assert r[0]["description"] == "updated description v2 !"


@patch("pyinaturalist.rest_api.ensure_file_objs")
@patch("pyinaturalist.rest_api.put")
def test_update_observation__local_photo(put, ensure_file_objs):
    update_observation(1234, access_token="token", local_photos="photo.jpg")

    # Make sure local_photos is replaced with the output of ensure_file_objs
    called_params = put.call_args[1]["json"]["observation"]
    assert called_params["local_photos"] == ensure_file_objs.return_value


def test_update_nonexistent_observation(requests_mock):
    """When we try to update a non-existent observation, iNat returns an error 410 with
    "observation does not exist"
    """
    requests_mock.put(
        f"{INAT_BASE_URL}/observations/999999999.json",
        json={"error": "Cette observation n’existe plus."},
        status_code=410,
    )

    params = {
        "ignore_photos": 1,
        "description": "updated description v2 !",
    }

    with pytest.raises(HTTPError) as excinfo:
        update_observation(999999999, access_token="valid token", **params)
    assert excinfo.value.response.status_code == 410
    assert excinfo.value.response.json() == {"error": "Cette observation n’existe plus."}


def test_update_observation_not_mine(requests_mock):
    """When we try to update the obs of another user, iNat returns an error 410 with "obs does not longer exists"."""
    requests_mock.put(
        f"{INAT_BASE_URL}/observations/16227955.json",
        json={"error": "Cette observation n’existe plus."},
        status_code=410,
    )

    params = {
        "ignore_photos": 1,
        "description": "updated description v2 !",
    }

    with pytest.raises(HTTPError) as excinfo:
        update_observation(16227955, access_token="valid token for another user", **params)
    assert excinfo.value.response.status_code == 410
    assert excinfo.value.response.json() == {"error": "Cette observation n’existe plus."}


def test_create_observation(requests_mock):
    requests_mock.post(
        f"{INAT_BASE_URL}/observations.json",
        json=load_sample_data("create_observation_result.json"),
        status_code=200,
    )

    r = create_observation(species_guess="Pieris rapae", access_token="valid token")
    assert len(r) == 1  # We added a single one
    assert r[0]["latitude"] is None
    assert r[0]["taxon_id"] == 55626  # Pieris Rapae @ iNaturalist


@patch("pyinaturalist.rest_api.ensure_file_objs")
@patch("pyinaturalist.rest_api.post")
def test_create_observation__local_photo(post, ensure_file_objs):
    create_observation(access_token="token", local_photos="photo.jpg")

    # Make sure local_photos is replaced with the output of ensure_file_objs
    called_params = post.call_args[1]["json"]["observation"]
    assert called_params["local_photos"] == ensure_file_objs.return_value


def test_create_observation_fail(requests_mock):
    params = {
        "species_guess": "Pieris rapae",
        # Some invalid data so the observation is rejected...
        "observed_on_string": (datetime.now() + timedelta(days=1)).isoformat(),
        "latitude": 200,
    }

    requests_mock.post(
        f"{INAT_BASE_URL}/observations.json",
        json=load_sample_data("create_observation_fail.json"),
        status_code=422,
    )

    with pytest.raises(HTTPError) as excinfo:
        create_observation(access_token="valid token", **params)
    assert excinfo.value.response.status_code == 422
    assert "errors" in excinfo.value.response.json()  # iNat also give details about the errors


def test_add_photo_to_observation(requests_mock):
    requests_mock.post(
        f"{INAT_BASE_URL}/observation_photos",
        json=load_sample_data("add_photo_to_observation.json"),
        status_code=200,
    )

    response = add_photo_to_observation(1234, BytesIO(), access_token="token")
    assert response["id"] == 1234
    assert response["created_at"] == "2020-09-24T21:06:16.964-05:00"
    assert response["photo"]["native_username"] == "username"


def test_delete_observation(requests_mock):
    requests_mock.delete(f"{INAT_BASE_URL}/observations/24774619.json", status_code=200)
    response = delete_observation(observation_id=24774619, access_token="valid token")
    assert response is None


def test_delete_unexisting_observation(requests_mock):
    """ObservationNotFound is raised if the observation doesn't exists"""
    requests_mock.delete(f"{INAT_BASE_URL}/observations/24774619.json", status_code=404)

    with pytest.raises(ObservationNotFound):
        delete_observation(observation_id=24774619, access_token="valid token")
