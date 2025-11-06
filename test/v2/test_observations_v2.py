import json
from io import BytesIO
from unittest.mock import patch

import pytest

from pyinaturalist.constants import API_V2
from pyinaturalist.session import ClientSession, MockResponse
from pyinaturalist.v2 import get_observations, upload
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


@patch('requests.sessions.Session.send')
def test_get_observations__except_fields(mock_send):
    get_observations(id=57707611, except_fields=['identifications'])
    request_obj = mock_send.call_args[0][0]
    json_body = json.loads(request_obj.body.decode())
    assert len(json_body['fields'].keys()) == 44
    assert 'identifications' not in json_body['fields']


def test_get_observations__all_pages(requests_mock):
    requests_mock.get(
        f'{API_V2}/observations',
        [
            {'json': SAMPLE_DATA['get_observations_node_page1'], 'status_code': 200},
            {'json': SAMPLE_DATA['get_observations_node_page2'], 'status_code': 200},
        ],
    )

    observations = get_observations(id=[57754375, 57707611], per_page=1, page='all')
    assert len(observations['results']) == 2


def test_get_observations__all_pages__post(requests_mock):
    requests_mock.post(
        f'{API_V2}/observations',
        [
            {'json': SAMPLE_DATA['get_observations_node_page1'], 'status_code': 200},
            {'json': SAMPLE_DATA['get_observations_node_page2'], 'status_code': 200},
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
