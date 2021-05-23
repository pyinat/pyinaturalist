from datetime import datetime
from dateutil.tz import tzutc

from pyinaturalist.constants import API_V1_BASE_URL
from pyinaturalist.v1 import get_projects, get_projects_by_id
from test.conftest import load_sample_data


def test_get_projects(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/projects',
        json=load_sample_data('get_projects.json'),
        status_code=200,
    )

    response = get_projects(q='invasive', lat=49.27, lng=-123.08, radius=400, order_by='distance')
    first_result = response['results'][0]

    assert response['total_results'] == len(response['results']) == 5
    assert first_result['id'] == 8291
    assert first_result['title'] == 'PNW Invasive Plant EDDR'
    assert first_result['is_umbrella'] is False
    assert len(first_result['user_ids']) == 33
    assert first_result['created_at'] == datetime(2016, 7, 20, 23, 0, 5, tzinfo=tzutc())
    assert first_result['updated_at'] == datetime(2020, 7, 28, 20, 9, 49, tzinfo=tzutc())


def test_get_projects_by_id(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/projects/8348,6432',
        json=load_sample_data('get_projects_by_id.json'),
        status_code=200,
    )
    response = get_projects_by_id([8348, 6432])
    first_result = response['results'][0]

    assert response['total_results'] == len(response['results']) == 2
    assert first_result['id'] == 8348
    assert first_result['title'] == 'Tucson High Native and Invasive Species Inventory'
    assert first_result['place_id'] == 96103
    assert first_result['location'] == [32.2264416406, -110.9617278383]
    assert first_result['created_at'] == datetime(2016, 7, 26, 23, 8, 47, tzinfo=tzutc())
    assert first_result['updated_at'] == datetime(2017, 9, 16, 1, 51, 1, tzinfo=tzutc())
