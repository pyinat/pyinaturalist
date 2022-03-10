from datetime import datetime
from unittest.mock import patch

from dateutil.tz import tzutc

from pyinaturalist.constants import API_V1_BASE_URL
from pyinaturalist.v1 import (
    add_project_observation,
    delete_project_observation,
    get_projects,
    get_projects_by_id,
    update_project,
)
from test.sample_data import SAMPLE_DATA


def test_get_projects(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/projects',
        json=SAMPLE_DATA['get_projects'],
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
        json=SAMPLE_DATA['get_projects_by_id'],
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


def test_add_project_observation(requests_mock):
    requests_mock.post(
        f'{API_V1_BASE_URL}/project_observations',
        json=SAMPLE_DATA['add_project_observation'],
        status_code=200,
    )
    response = add_project_observation(project_id=1234, observation_id=5678, access_token='token')
    assert response['id'] == 54986584


def test_delete_project_observation(requests_mock):
    requests_mock.delete(
        f'{API_V1_BASE_URL}/projects/1234/remove',
        status_code=200,
    )
    response = delete_project_observation(
        project_id=1234, observation_id=5678, access_token='token'
    )
    assert response.status_code == 200


@patch('pyinaturalist.v1.projects.put_v1')
def test_update_project(mock_put):
    update_project(1234, title='New Title', description='New Description')

    request_args = mock_put.call_args[1]
    project_params = request_args['json']['project']
    assert request_args['timeout'] == 60
    assert project_params['title'] == 'New Title'
    assert project_params['description'] == 'New Description'


@patch('pyinaturalist.v1.projects.put_v1')
def test_update_project__remove_users(mock_put, requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/projects/1234',
        json=SAMPLE_DATA['get_projects'],
        status_code=200,
    )
    update_project(1234, remove_users=[5678])

    project_params = mock_put.call_args[1]['json']['project']
    rules = project_params['project_observation_rules_attributes']
    assert rules[0]['operand_id'] == 1234 and not rules[0].get('_destroy')
    assert rules[1]['operand_id'] == 5678 and rules[1]['_destroy'] is True
