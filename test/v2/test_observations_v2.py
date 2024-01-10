import json
from unittest.mock import patch

import pytest

from pyinaturalist.constants import API_V2
from pyinaturalist.session import ClientSession, MockResponse
from pyinaturalist.v2 import get_observations
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
