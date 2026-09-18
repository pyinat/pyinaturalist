import json
from datetime import datetime
from unittest.mock import patch

import pytest
from dateutil.tz import tzutc

from pyinaturalist.client.session import ClientSession, MockResponse
from pyinaturalist.constants import API_V2
from pyinaturalist.exceptions import ObservationNotFound
from pyinaturalist.v2 import (
    add_project_observation,
    delete_project_observation,
    get_projects,
    get_projects_by_id,
)
from test.sample_data import SAMPLE_DATA

OBS_UUID = '2cd5e678-7383-4793-b325-bd9e29f4cf9c'
PROJECT_OBS_UUID_1 = 'fdb6f20e-9476-4bcd-a12b-79dbe4e4ece3'
PROJECT_OBS_UUID_2 = 'e6e91e54-e61d-4e95-8c90-032789f3481d'
OBS_WITH_PROJECTS = {
    'total_results': 1,
    'results': [
        {
            'uuid': OBS_UUID,
            'project_observations': [
                {'id': 1, 'uuid': PROJECT_OBS_UUID_1, 'project': {'id': 2420}},
                {'id': 2, 'uuid': PROJECT_OBS_UUID_2, 'project': {'id': 407}},
            ],
        }
    ],
}


def test_get_projects__minimal(requests_mock):
    requests_mock.get(
        f'{API_V2}/projects',
        json=SAMPLE_DATA['get_projects_minimal'],
        status_code=200,
    )

    projects = get_projects(q='invasive')
    assert projects['total_results'] == 1248
    assert projects['results'][0]['id'] == 3218


def test_get_projects__all_fields(requests_mock):
    requests_mock.get(
        f'{API_V2}/projects',
        json=SAMPLE_DATA['get_projects_by_id'],
        status_code=200,
    )

    projects = get_projects(q='invasive', fields='all')
    first_result = projects['results'][0]
    assert first_result['id'] == 8348
    assert first_result['title'] == 'Tucson High Native and Invasive Species Inventory'
    assert first_result['location'] == [32.2264416406, -110.9617278383]
    assert first_result['created_at'] == datetime(2016, 7, 26, 23, 8, 47, tzinfo=tzutc())


def test_get_projects__some_fields(requests_mock):
    requests_mock.post(
        f'{API_V2}/projects',
        json=SAMPLE_DATA['get_projects_by_id'],
        status_code=200,
    )

    projects = get_projects(q='invasive', fields={'title': True, 'slug': True})
    assert projects['results'][0]['id'] == 8348
    assert requests_mock.request_history[0].headers['X-HTTP-Method-Override'] == 'GET'
    assert requests_mock.request_history[0].json()['fields'] == {'title': True, 'slug': True}


@patch('pyinaturalist.client.session.format_response')
@patch('requests.sessions.Session.send')
def test_get_projects__except_fields(mock_send, mock_format):
    get_projects(q='invasive', except_fields=['admins'])
    request_obj = mock_send.call_args[0][0]
    json_body = json.loads(request_obj.body.decode())
    assert 'admins' not in json_body['fields']
    assert 'title' in json_body['fields']


def test_get_projects__invalid_fields():
    with pytest.raises(ValueError):
        get_projects(q='invasive', fields=['title'], except_fields=['admins'])


def test_get_projects__invalid_order_by():
    with pytest.raises(ValueError):
        get_projects(q='invasive', order_by='title')


def test_get_projects__all_pages(requests_mock):
    requests_mock.get(
        f'{API_V2}/projects',
        [
            {'json': SAMPLE_DATA['get_projects_minimal'], 'status_code': 200},
            {'json': {**SAMPLE_DATA['get_projects_minimal'], 'results': []}, 'status_code': 200},
        ],
    )

    projects = get_projects(q='invasive', per_page=2, page='all')
    assert len(projects['results']) == 2


def test_get_projects_by_id__all_fields(requests_mock):
    requests_mock.get(
        f'{API_V2}/projects/8348',
        json=SAMPLE_DATA['get_projects_by_id'],
        status_code=200,
    )

    projects = get_projects_by_id(8348, fields='all')
    first_result = projects['results'][0]
    assert projects['total_results'] == 1
    assert first_result['id'] == 8348
    assert first_result['place_id'] == 96103
    assert first_result['location'] == [32.2264416406, -110.9617278383]
    assert first_result['created_at'] == datetime(2016, 7, 26, 23, 8, 47, tzinfo=tzutc())
    assert first_result['updated_at'] == datetime.fromisoformat('2024-12-07T15:01:08-07:00')


def test_get_projects_by_id__some_fields(requests_mock):
    requests_mock.post(
        f'{API_V2}/projects',
        json=SAMPLE_DATA['get_projects_by_id'],
        status_code=200,
    )

    projects = get_projects_by_id([8348, 6432], fields=['title'])
    assert projects['results'][0]['id'] == 8348
    assert requests_mock.request_history[0].json()['id'] == [8348, 6432]


@pytest.mark.parametrize(
    'n_ids, expected_method',
    [(1, 'GET'), (30, 'GET'), (31, 'POST')],
)
@patch.object(ClientSession, 'send', return_value=MockResponse())
def test_get_projects_by_id__many_ids(mock_send, n_ids, expected_method):
    """If requesting more than MAX_IDS_PER_REQUEST IDs, they should be sent via POST body"""
    get_projects_by_id(list(range(1, n_ids + 1)))
    assert mock_send.call_args[0][0].method == expected_method


def test_add_project_observation(requests_mock):
    requests_mock.post(
        f'{API_V2}/project_observations',
        json={'total_results': 1, 'results': [{'id': 54986584, 'uuid': PROJECT_OBS_UUID_1}]},
        status_code=200,
    )

    response = add_project_observation(2420, OBS_UUID, access_token='token')
    assert response['results'][0]['id'] == 54986584
    assert len(requests_mock.request_history) == 1
    assert requests_mock.request_history[0].json() == {
        'project_observation': {'project_id': 2420, 'observation_id': OBS_UUID}
    }


def test_add_project_observation__by_id(requests_mock):
    """A numeric observation ID should be resolved to a UUID before adding it to the project"""
    requests_mock.post(
        f'{API_V2}/observations',
        json={'total_results': 1, 'results': [{'uuid': OBS_UUID}]},
        status_code=200,
    )
    requests_mock.post(
        f'{API_V2}/project_observations',
        json={'total_results': 1, 'results': [{'id': 54986584}]},
        status_code=200,
    )

    add_project_observation(2420, 149358362, access_token='token')
    lookup_request, add_request = requests_mock.request_history
    assert lookup_request.url == f'{API_V2}/observations'
    assert lookup_request.json()['id'] == 149358362
    assert add_request.json()['project_observation']['observation_id'] == OBS_UUID


def test_delete_project_observation(requests_mock):
    requests_mock.post(f'{API_V2}/observations', json=OBS_WITH_PROJECTS, status_code=200)
    requests_mock.delete(f'{API_V2}/project_observations/{PROJECT_OBS_UUID_2}', status_code=200)

    response = delete_project_observation(407, OBS_UUID, access_token='token')
    assert response is None
    lookup_request, delete_request = requests_mock.request_history
    assert lookup_request.json()['uuid'] == OBS_UUID
    assert delete_request.method == 'DELETE'
    assert delete_request.url == f'{API_V2}/project_observations/{PROJECT_OBS_UUID_2}'


@pytest.mark.parametrize(
    'response_json, project_id, expected_exception',
    [
        (OBS_WITH_PROJECTS, 1234, ValueError),
        ({'total_results': 0, 'results': []}, 407, ObservationNotFound),
    ],
    ids=['not_in_project', 'not_found'],
)
def test_delete_project_observation__errors(
    requests_mock, response_json, project_id, expected_exception
):
    requests_mock.post(f'{API_V2}/observations', json=response_json, status_code=200)

    with pytest.raises(expected_exception):
        delete_project_observation(project_id, OBS_UUID, access_token='token')
