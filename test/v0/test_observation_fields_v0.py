from datetime import datetime

from dateutil.tz import tzutc

from pyinaturalist.constants import API_V0
from pyinaturalist.v0 import get_observation_fields, put_observation_field_values
from test.sample_data import SAMPLE_DATA


def test_get_observation_fields(requests_mock):
    """get_observation_fields() work as expected (basic use)"""
    requests_mock.get(
        f'{API_V0}/observation_fields.json?q=sex',
        json=SAMPLE_DATA['get_observation_fields_page2'],
        status_code=200,
    )

    response = get_observation_fields(q='sex', page=2)
    first_result = response['results'][0]
    assert len(response['results']) == 3
    assert first_result['id'] == 5
    assert first_result['datatype'] == 'text'
    assert first_result['created_at'] == datetime(2012, 1, 23, 8, 12, 0, 138000, tzinfo=tzutc())
    assert first_result['updated_at'] == datetime(2018, 10, 16, 6, 47, 43, 975000, tzinfo=tzutc())


def test_get_observation_fields__all_pages(requests_mock):
    page_1_json_response = SAMPLE_DATA['get_observation_fields_page1']
    page_2_json_response = SAMPLE_DATA['get_observation_fields_page2']

    requests_mock.get(
        f'{API_V0}/observation_fields.json',
        [
            {'json': page_1_json_response, 'status_code': 200},
            {'json': page_2_json_response, 'status_code': 200},
            {'json': [], 'status_code': 200},
        ],
    )
    expected_results = page_1_json_response + page_2_json_response

    response = get_observation_fields(q='sex', page='all')
    first_result = response['results'][0]
    assert response['total_results'] == len(response['results']) == len(expected_results)
    assert first_result['created_at'] == datetime(2016, 5, 29, 16, 17, 8, 51000, tzinfo=tzutc())
    assert first_result['updated_at'] == datetime(2018, 1, 1, 1, 17, 56, 7000, tzinfo=tzutc())


def test_put_observation_field_values(requests_mock):
    requests_mock.put(
        f'{API_V0}/observation_field_values/31',
        json=SAMPLE_DATA['post_put_observation_field_value'],
        status_code=200,
    )

    response = put_observation_field_values(
        observation_id=18166477,
        observation_field_id=31,  # Animal behavior
        value='fouraging',
        access_token='valid token',
    )

    assert response['id'] == 31
    assert response['observation_field_id'] == 31
    assert response['observation_id'] == 18166477
    assert response['value'] == 'fouraging'
