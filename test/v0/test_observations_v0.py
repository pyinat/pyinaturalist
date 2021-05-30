import pytest
from datetime import datetime, timedelta
from dateutil.tz import tzutc
from io import BytesIO
from unittest.mock import patch

from requests import HTTPError

from pyinaturalist.constants import API_V0_BASE_URL
from pyinaturalist.exceptions import ObservationNotFound
from pyinaturalist.request_params import OBSERVATION_FORMATS
from pyinaturalist.v0 import (
    add_photo_to_observation,
    add_sound_to_observation,
    create_observation,
    delete_observation,
    get_observations,
    update_observation,
)
from test.conftest import load_sample_data


def get_observations_response(response_format):
    response_format = response_format.replace('widget', 'js')
    return load_sample_data(f'get_observations.{response_format}')


@pytest.mark.parametrize('response_format', OBSERVATION_FORMATS)
def test_get_observations(response_format, requests_mock):
    """Test all supported observation data formats"""
    mock_response = get_observations_response(response_format)
    key = 'json' if response_format == 'json' else 'text'

    requests_mock.get(
        f'{API_V0_BASE_URL}/observations.{response_format}',
        status_code=200,
        **{key: mock_response},
    )

    observations = get_observations(taxon_id=493595, response_format=response_format)

    # For JSON format, ensure type conversions were performed
    if response_format == 'json':
        assert observations[0]['latitude'] == 50.646894
        assert observations[0]['longitude'] == 4.360086
        assert observations[0]['created_at'] == datetime(2018, 9, 5, 12, 31, 8, 48000, tzinfo=tzutc())
        assert observations[0]['updated_at'] == datetime(2018, 9, 22, 17, 19, 27, 80000, tzinfo=tzutc())
    else:
        assert observations == mock_response


@pytest.mark.parametrize('response_format', ['geojson', 'yaml'])
def test_get_observations__invalid_format(response_format):
    with pytest.raises(ValueError):
        get_observations(taxon_id=493595, response_format=response_format)


def test_create_observation(requests_mock):
    requests_mock.post(
        f'{API_V0_BASE_URL}/observations.json',
        json=load_sample_data('create_observation_result.json'),
        status_code=200,
    )

    response = create_observation(species_guess='Pieris rapae', access_token='valid token')
    assert len(response) == 1
    assert response[0]['latitude'] is None
    assert response[0]['taxon_id'] == 55626


@patch('pyinaturalist.v0.observations.add_photo_to_observation')
@patch('pyinaturalist.v0.observations.post')
def test_create_observation__with_photos(post, mock_add_photo):
    create_observation(access_token='token', photos=['photo_1.jpg', 'photo_2.jpg'])

    assert 'local_photos' not in post.call_args[1]['json']['observation']
    assert mock_add_photo.call_count == 2


@patch('pyinaturalist.v0.observations.add_sound_to_observation')
@patch('pyinaturalist.v0.observations.post')
def test_create_observation__with_sounds(post, mock_add_sound):
    create_observation(access_token='token', sounds=['sound_1.mp3', 'sound_2.wav'])

    assert 'sounds' not in post.call_args[1]['json']['observation']
    assert mock_add_sound.call_count == 2


def test_create_observation_fail(requests_mock):
    params = {
        'species_guess': 'Pieris rapae',
        # Some invalid data so the observation is rejected...
        'observed_on_string': (datetime.now() + timedelta(days=1)).isoformat(),
        'latitude': 200,
    }

    requests_mock.post(
        f'{API_V0_BASE_URL}/observations.json',
        json=load_sample_data('create_observation_fail.json'),
        status_code=422,
    )

    with pytest.raises(HTTPError) as excinfo:
        create_observation(access_token='valid token', **params)
    assert excinfo.value.response.status_code == 422
    assert 'errors' in excinfo.value.response.json()  # iNat also give details about the errors


def test_update_observation(requests_mock):
    requests_mock.put(
        f'{API_V0_BASE_URL}/observations/17932425.json',
        json=load_sample_data('update_observation_result.json'),
        status_code=200,
    )

    params = {
        'ignore_photos': 1,
        'description': 'updated description v2 !',
    }
    response = update_observation(17932425, access_token='valid token', **params)

    # If all goes well we got a single element representing the updated observation, enclosed in a list.
    assert len(response) == 1
    assert response[0]['id'] == 17932425
    assert response[0]['description'] == 'updated description v2 !'


@patch('pyinaturalist.v0.observations.add_photo_to_observation')
@patch('pyinaturalist.v0.observations.put')
def test_update_observation__local_photo(put, mock_add_photo):
    update_observation(1234, access_token='token', local_photos='photo.jpg')

    assert 'local_photos' not in put.call_args[1]['json']['observation']
    assert mock_add_photo.call_count == 1


def test_update_nonexistent_observation(requests_mock):
    """When we try to update a non-existent observation, iNat returns an error 410 with
    'observation does not exist'
    """
    requests_mock.put(
        f'{API_V0_BASE_URL}/observations/999999999.json',
        json={'error': 'Cette observation n’existe plus.'},
        status_code=410,
    )

    params = {
        'ignore_photos': 1,
        'description': 'updated description v2 !',
    }

    with pytest.raises(HTTPError) as excinfo:
        update_observation(999999999, access_token='valid token', **params)
    assert excinfo.value.response.status_code == 410
    assert excinfo.value.response.json() == {'error': 'Cette observation n’existe plus.'}


def test_update_observation_not_mine(requests_mock):
    """When we try to update the obs of another user, iNat returns an error 410 with 'obs does not longer exists'."""
    requests_mock.put(
        f'{API_V0_BASE_URL}/observations/16227955.json',
        json={'error': 'Cette observation n’existe plus.'},
        status_code=410,
    )

    params = {
        'ignore_photos': 1,
        'description': 'updated description v2 !',
    }

    with pytest.raises(HTTPError) as excinfo:
        update_observation(16227955, access_token='valid token for another user', **params)
    assert excinfo.value.response.status_code == 410
    assert excinfo.value.response.json() == {'error': 'Cette observation n’existe plus.'}


def test_add_photo_to_observation(requests_mock):
    requests_mock.post(
        f'{API_V0_BASE_URL}/observation_photos',
        json=load_sample_data('post_observation_photos.json'),
        status_code=200,
    )

    response = add_photo_to_observation(1234, BytesIO(), access_token='token')
    assert response['id'] == 1234
    assert response['created_at'] == '2020-09-24T21:06:16.964-05:00'
    assert response['photo']['native_username'] == 'username'


def test_add_sound_to_observation(requests_mock):
    requests_mock.post(
        f'{API_V0_BASE_URL}/observation_sounds',
        json=load_sample_data('post_observation_sounds.json'),
        status_code=200,
    )

    response = add_sound_to_observation(233946, BytesIO(), access_token='token')
    assert response['id'] == 233946
    assert response['created_at'] == '2021-05-30T17:36:40.286-05:00'
    assert response['sound']['file_content_type'] == 'audio/mpeg'


def test_delete_observation(requests_mock):
    requests_mock.delete(f'{API_V0_BASE_URL}/observations/24774619.json', status_code=200)
    response = delete_observation(observation_id=24774619, access_token='valid token')
    assert response is None


def test_delete_unexisting_observation(requests_mock):
    """ObservationNotFound is raised if the observation doesn't exists"""
    requests_mock.delete(f'{API_V0_BASE_URL}/observations/24774619.json', status_code=404)

    with pytest.raises(ObservationNotFound):
        delete_observation(observation_id=24774619, access_token='valid token')
