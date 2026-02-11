import json
from io import BytesIO
from unittest.mock import patch

import pytest

from pyinaturalist.constants import API_V2
from pyinaturalist.exceptions import ObservationNotFound
from pyinaturalist.session import ClientSession, MockResponse
from pyinaturalist.v2 import (
    create_observation,
    delete_observation,
    get_observations,
    set_observation_field,
    update_observation,
    upload,
)
from test.sample_data import SAMPLE_DATA


def test_get_observations__minimal(requests_mock):
    requests_mock.get(
        f'{API_V2}/observations',
        json=SAMPLE_DATA['get_observations_v2_minimal'],
        status_code=200,
    )

    observations = get_observations(id=14150125)
    assert observations['results'][0] == {
        'uuid': '91a29d5f-d2bf-47ff-b629-d0b79d51e46c',
        'created_at': None,
    }


def test_get_observations__all_fields(requests_mock):
    requests_mock.get(
        f'{API_V2}/observations',
        json=SAMPLE_DATA['get_observations_v2_full'],
        status_code=200,
    )

    observations = get_observations(id=14150125, fields='all')
    assert observations['results'][0]['id'] == 14150125
    assert observations['results'][0]['species_guess'] == 'Common Loon'
    assert len(observations['results'][0].keys()) == 66


def test_get_observations__some_fields(requests_mock):
    requests_mock.post(
        f'{API_V2}/observations',
        json=SAMPLE_DATA['get_observations_v2_full'],
        status_code=200,
    )

    observations = get_observations(id=57707611, fields=['id', 'species_guess'])
    assert observations['results'][0]['id'] == 14150125
    assert observations['results'][0]['species_guess'] == 'Common Loon'


@patch('pyinaturalist.session.format_response')
@patch('requests.sessions.Session.send')
def test_get_observations__except_fields(mock_send, mock_format):
    get_observations(id=57707611, except_fields=['identifications'])
    request_obj = mock_send.call_args[0][0]
    json_body = json.loads(request_obj.body.decode())
    assert len(json_body['fields'].keys()) == 47
    assert 'identifications' not in json_body['fields']


def test_get_observations__all_pages(requests_mock):
    requests_mock.get(
        f'{API_V2}/observations',
        [
            {'json': SAMPLE_DATA['get_observations_v1_page1'], 'status_code': 200},
            {'json': SAMPLE_DATA['get_observations_v1_page2'], 'status_code': 200},
        ],
    )

    observations = get_observations(id=[57754375, 57707611], per_page=1, page='all')
    assert len(observations['results']) == 2


def test_get_observations__all_pages__post(requests_mock):
    requests_mock.post(
        f'{API_V2}/observations',
        [
            {'json': SAMPLE_DATA['get_observations_v1_page1'], 'status_code': 200},
            {'json': SAMPLE_DATA['get_observations_v1_page2'], 'status_code': 200},
        ],
    )

    observations = get_observations(
        id=[57754375, 57707611],
        per_page=1,
        page='all',
        fields=['species_guess'],
    )
    assert len(observations['results']) == 2


@pytest.mark.parametrize(
    'n_ids, expected_method',
    [(1, 'GET'), (30, 'GET'), (31, 'POST'), (200, 'POST')],
)
@patch.object(ClientSession, 'send', return_value=MockResponse())
def test_get_observations__by_id(mock_send, n_ids, expected_method):
    """If requesting more than MAX_IDS_PER_REQUEST IDs, they should be sent via POST body"""
    get_observations(id=list(range(n_ids)))
    assert mock_send.call_args[0][0].method == expected_method


@patch.object(ClientSession, 'send', return_value=MockResponse())
def test_get_observations__by_obs_field(mock_send):
    get_observations(taxon_id=3, observation_fields=['Species count'])
    request = mock_send.call_args[0][0]
    assert request.params == {'taxon_id': '3', 'field:Species count': ''}


@patch.object(ClientSession, 'send', return_value=MockResponse())
def test_get_observations__by_obs_field_values(mock_send):
    get_observations(taxon_id=3, observation_fields={'Species count': 2})
    request = mock_send.call_args[0][0]
    assert request.params == {'taxon_id': '3', 'field:Species count': '2'}


def test_get_observations__invalid_fields():
    with pytest.raises(ValueError):
        get_observations(taxon_id=3, fields=['taxon'], except_fields=['identifications'])


def test_upload(requests_mock):
    """Test uploading photos and sounds to an observation"""
    requests_mock.post(
        f'{API_V2}/observation_photos',
        json=SAMPLE_DATA['post_observation_media_v2'],
        status_code=200,
    )
    requests_mock.post(
        f'{API_V2}/observation_sounds',
        json=SAMPLE_DATA['post_observation_media_v2'],
        status_code=200,
    )

    response = upload(
        '53411fc2-bdf0-434e-afce-4dac33970173',
        photos=BytesIO(b'123456'),
        sounds=BytesIO(b'123456'),
        access_token='token',
    )
    assert response[0]['id'] == 123456
    assert response[1]['id'] == 123456


def test_upload__with_photo_ids(requests_mock):
    """Test attaching existing photos to an observation"""
    requests_mock.post(
        f'{API_V2}/observation_photos',
        json=SAMPLE_DATA['post_observation_media_v2'],
        status_code=200,
    )

    response = upload(
        '53411fc2-bdf0-434e-afce-4dac33970173',
        access_token='token',
        photo_ids=[5678, 9012],
    )
    assert len(response) == 2
    # Verify the request was made with correct JSON body
    history = requests_mock.request_history
    for request in history:
        assert (
            request.json()['observation_photo']['observation_id']
            == '53411fc2-bdf0-434e-afce-4dac33970173'
        )


def test_create_observation(requests_mock):
    test_uuid = '53411fc2-bdf0-434e-afce-4dac33970173'
    requests_mock.post(
        f'{API_V2}/observations',
        json={
            'total_results': 1,
            'results': [
                {
                    'uuid': test_uuid,
                    'id': 123456,
                    'species_guess': 'Pieris rapae',
                    'observed_on_string': '2020-09-01',
                }
            ],
        },
        status_code=200,
    )

    response = create_observation(
        species_guess='Pieris rapae', observed_on='2020-09-01', access_token='token'
    )
    assert response['uuid'] == test_uuid
    assert response['id'] == 123456


@patch('pyinaturalist.v2.observations.upload')
@patch('pyinaturalist.v2.observations.post')
def test_create_observation__with_files(mock_post, mock_upload):
    test_uuid = '53411fc2-bdf0-434e-afce-4dac33970173'
    mock_post.return_value.json.return_value = {'results': [{'uuid': test_uuid, 'id': 123456}]}

    create_observation(
        access_token='token',
        photos=['photo_1.jpg', 'photo_2.jpg'],
        sounds=['sound_1.mp3', 'sound_2.wav'],
        photo_ids=[12345],
    )

    request_params = mock_post.call_args[1]['json']['observation']
    assert 'local_photos' not in request_params
    assert 'photos' not in request_params
    assert 'sounds' not in request_params
    assert 'photo_ids' not in request_params

    # Verify upload was called with the correct files
    mock_upload.assert_called_once()
    upload_args = mock_upload.call_args
    assert upload_args[0][0] == test_uuid
    assert upload_args[1]['photos'] == ['photo_1.jpg', 'photo_2.jpg']
    assert upload_args[1]['sounds'] == ['sound_1.mp3', 'sound_2.wav']
    assert upload_args[1]['photo_ids'] == [12345]


@patch('pyinaturalist.v2.observations.set_observation_field')
@patch('pyinaturalist.v2.observations.post')
def test_create_observation__with_observation_fields(mock_post, mock_set_field):
    """Observation fields should be added in separate requests"""
    test_uuid = '53411fc2-bdf0-434e-afce-4dac33970173'
    mock_post.return_value.json.return_value = {'results': [{'uuid': test_uuid, 'id': 123456}]}

    create_observation(
        access_token='token',
        species_guess='Pieris rapae',
        observation_fields={297: 1, 567: 'test value'},
    )

    # Observation fields should not be in the create request body
    request_params = mock_post.call_args[1]['json']['observation']
    assert 'observation_field_values_attributes' not in request_params
    assert 'observation_fields' not in request_params
    assert mock_set_field.call_count == 2


def test_update_observation(requests_mock):
    test_uuid = '53411fc2-bdf0-434e-afce-4dac33970173'
    requests_mock.put(
        f'{API_V2}/observations/{test_uuid}',
        json={
            'total_results': 1,
            'results': [
                {
                    'uuid': test_uuid,
                    'id': 123456,
                    'description': 'updated description!',
                }
            ],
        },
        status_code=200,
    )

    response = update_observation(
        test_uuid, access_token='token', description='updated description!'
    )

    assert response['uuid'] == test_uuid
    assert response['description'] == 'updated description!'


@patch('pyinaturalist.v2.observations.upload')
@patch('pyinaturalist.v2.observations.put')
def test_update_observation__with_photos(mock_put, mock_upload):
    test_uuid = '53411fc2-bdf0-434e-afce-4dac33970173'
    mock_put.return_value.json.return_value = {'results': [{'uuid': test_uuid}]}

    update_observation(test_uuid, access_token='token', photos='photo.jpg')

    request_args = mock_put.call_args[1]
    obs_params = request_args['json']['observation']
    assert request_args['ignore_photos'] == 1
    assert 'local_photos' not in obs_params
    assert 'photos' not in obs_params
    assert 'sounds' not in obs_params
    mock_upload.assert_called_once()


@patch('pyinaturalist.v2.observations.set_observation_field')
@patch('pyinaturalist.v2.observations.put')
def test_update_observation__with_observation_fields(mock_put, mock_set_field):
    """Observation fields should be added in separate requests"""
    test_uuid = '53411fc2-bdf0-434e-afce-4dac33970173'
    mock_put.return_value.json.return_value = {'results': [{'uuid': test_uuid}]}

    update_observation(
        test_uuid,
        access_token='token',
        observation_fields={297: 1},
    )

    # Observation fields should not be in the update request body
    obs_params = mock_put.call_args[1]['json']['observation']
    assert 'observation_field_values_attributes' not in obs_params
    mock_set_field.assert_called_once()


def test_set_observation_field(requests_mock):
    test_uuid = '53411fc2-bdf0-434e-afce-4dac33970173'
    requests_mock.post(
        f'{API_V2}/observation_field_values',
        json={'results': [{'uuid': 'ofv-uuid-1'}]},
        status_code=200,
    )

    response = set_observation_field(
        test_uuid,
        observation_field_id=297,
        value=1,
        access_token='token',
    )

    assert response == {'results': [{'uuid': 'ofv-uuid-1'}]}
    assert len(requests_mock.request_history) == 1
    body = requests_mock.request_history[0].json()
    assert body == {
        'observation_field_value': {
            'observation_id': test_uuid,
            'observation_field_id': 297,
            'value': 1,
        }
    }


def test_delete_observation(requests_mock):
    test_uuid = '53411fc2-bdf0-434e-afce-4dac33970173'
    requests_mock.delete(f'{API_V2}/observations/{test_uuid}', status_code=200)
    response = delete_observation(observation_uuid=test_uuid, access_token='token')
    assert response is None


def test_delete_observation__not_found(requests_mock):
    test_uuid = '53411fc2-bdf0-434e-afce-4dac33970173'
    requests_mock.delete(f'{API_V2}/observations/{test_uuid}', status_code=404)
    with pytest.raises(ObservationNotFound):
        delete_observation(observation_uuid=test_uuid, access_token='token')
