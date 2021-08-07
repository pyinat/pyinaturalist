from datetime import datetime

from dateutil.tz import tzutc

from pyinaturalist.constants import API_V1_BASE_URL
from pyinaturalist.node_api import get_geojson_observations
from pyinaturalist.v1 import get_user_by_id, get_users_autocomplete
from test.conftest import load_sample_data


def test_get_user_by_id(requests_mock):
    user_id = 1
    requests_mock.get(
        f'{API_V1_BASE_URL}/users/{user_id}',
        json=load_sample_data('get_user_by_id.json'),
        status_code=200,
    )

    user = get_user_by_id(user_id)
    assert user['id'] == user_id
    assert user['created_at'] == datetime(2008, 3, 20, 21, 15, 42, tzinfo=tzutc())
    assert user['spam'] is False


def test_get_users_autocomplete(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/users/autocomplete',
        json=load_sample_data('get_users_autocomplete.json'),
        status_code=200,
    )

    response = get_users_autocomplete(q='niconoe')
    first_result = response['results'][0]

    assert len(response['results']) == response['total_results'] == 3
    assert first_result['id'] == 886482
    assert first_result['login'] == 'niconoe'
    assert first_result['created_at'] == datetime(2018, 4, 23, 17, 11, 14, tzinfo=tzutc())


# TODO: Deprecate get_geojson_observations and move to pyinaturalist-convert
def test_get_geojson_observations(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations',
        json=load_sample_data('get_observation.json'),
        status_code=200,
    )

    geojson = get_geojson_observations(id=16227955)
    feature = geojson['features'][0]
    assert feature['geometry']['coordinates'] == [4.360086, 50.646894]
    assert feature['properties']['id'] == 16227955
    assert feature['properties']['taxon_id'] == 493595


def test_get_geojson_observations__custom_properties(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations',
        json=load_sample_data('get_observation.json'),
        status_code=200,
    )

    properties = ['taxon_name', 'taxon_rank']
    geojson = get_geojson_observations(id=16227955, properties=properties)
    feature = geojson['features'][0]
    assert feature['properties']['taxon_name'] == 'Lixus bardanae'
    assert feature['properties']['taxon_rank'] == 'species'
    assert 'id' not in feature['properties'] and 'taxon_id' not in feature['properties']
