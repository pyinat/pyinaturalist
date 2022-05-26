from datetime import datetime

from dateutil.tz import tzoffset

from pyinaturalist.constants import API_V1
from pyinaturalist.v1 import get_identifications, get_identifications_by_id
from test.conftest import load_sample_data


def test_get_identifications(requests_mock):
    requests_mock.get(
        f'{API_V1}/identifications',
        json=load_sample_data('get_identifications.json'),
        status_code=200,
    )
    response = get_identifications()
    assert len(response['results']) == 2
    first_result = response['results'][0]
    expected_datetime = datetime(2021, 2, 18, 20, 31, 32, tzinfo=tzoffset(None, -21600))

    assert first_result['id'] == 155554373
    assert first_result['user']['id'] == 2115051
    assert first_result['taxon']['id'] == 60132
    assert first_result['created_at'] == expected_datetime
    assert first_result['current'] is True


def test_get_identifications_by_id(requests_mock):
    # Not much to test here, pretty much exactly the same as get_identifications()
    mock_response = load_sample_data('get_identifications.json')
    mock_response['results'] = [mock_response['results'][0]]
    requests_mock.get(
        f'{API_V1}/identifications/155554373',
        json=mock_response,
        status_code=200,
    )

    response = get_identifications_by_id(155554373)
    assert response['results'][0]['id'] == 155554373
