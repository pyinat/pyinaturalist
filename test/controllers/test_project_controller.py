# ruff: noqa: F405
from datetime import datetime
from unittest.mock import patch

from dateutil.tz import tzutc

from pyinaturalist.client import iNatClient
from pyinaturalist.constants import API_V2
from pyinaturalist.models import Project, ProjectObservationField, ProjectUser, User
from test.sample_data import SAMPLE_DATA, j_project_3_obs_fields, j_project_4

OBS_UUID = '2cd5e678-7383-4793-b325-bd9e29f4cf9c'
PROJECT_OBS_UUID = 'e6e91e54-e61d-4e95-8c90-032789f3481d'


def test_from_id(requests_mock):
    project_id = 8348
    requests_mock.get(
        f'{API_V2}/projects/{project_id}',
        json={'results': [j_project_4]},
        status_code=200,
    )
    result = iNatClient().projects(project_id)
    assert isinstance(result, Project)
    assert result.id == project_id


def test_from_ids(requests_mock):
    project_id = 8348
    requests_mock.get(
        f'{API_V2}/projects/{project_id}',
        json={'results': [j_project_4], 'total_results': 1},
        status_code=200,
    )
    results = iNatClient().projects.from_ids(project_id).all()
    project = results[0]
    assert len(results) == 1 and isinstance(project, Project)

    # All fields should be requested by default
    assert requests_mock.request_history[0].qs['fields'] == ['all']

    assert project.id == project_id
    assert project.location == (32.2264416406, -110.9617278383)
    assert project.project_observation_rules == project.obs_rules
    assert project.search_parameters[0]['field'] == 'quality_grade'
    assert project.user_ids == [84403, 311743]

    admin = project.admins[0]
    assert isinstance(admin, ProjectUser) and admin.id == 84403 and admin.role == 'manager'
    assert isinstance(project.user, User) and project.user.id == 84403


def test_search(requests_mock):
    requests_mock.get(
        f'{API_V2}/projects',
        json=SAMPLE_DATA['get_projects_by_id'],
        status_code=200,
    )
    results = (
        iNatClient()
        .projects.search(
            q='invasive',
            lat=32.22,
            lng=-110.96,
            radius=400,
            order_by='distance',
        )
        .all()
    )

    # All fields should be requested by default
    assert requests_mock.request_history[0].qs['fields'] == ['all']

    project = results[0]
    assert len(results) == 1 and isinstance(project, Project)
    assert project.id == 8348
    assert project.title == 'Tucson High Native and Invasive Species Inventory'
    assert project.is_umbrella is False
    assert project.created_at == datetime(2016, 7, 26, 23, 8, 47, tzinfo=tzutc())
    assert project.updated_at == datetime.fromisoformat('2024-12-07T15:01:08-07:00')


def test_search__with_obs_fields(requests_mock):
    requests_mock.get(
        f'{API_V2}/projects',
        json={'results': [j_project_3_obs_fields], 'total_results': 1},
        status_code=200,
    )
    results = iNatClient().projects.search(id=1234).all()
    obs_field = results[0].project_observation_fields[0]

    assert isinstance(obs_field, ProjectObservationField)
    assert obs_field.id == 30
    assert obs_field.position == 0
    assert obs_field.required is False


@patch('pyinaturalist.client.client.get_access_token', return_value='token')
def test_add_observations(get_access_token, requests_mock):
    requests_mock.post(
        f'{API_V2}/project_observations',
        json={'total_results': 1, 'results': [{'id': 54986584}]},
        status_code=200,
    )
    observation_uuids = [OBS_UUID, 'ec2e6a5c-3d43-4f5d-9d64-7b2b1b1cdb7f']
    responses = iNatClient().projects.add_observations(1234, observation_uuids)
    get_access_token.assert_called()

    assert len(responses) == 2
    requested_uuids = [
        request.json()['project_observation']['observation_id']
        for request in requests_mock.request_history
    ]
    assert requested_uuids == observation_uuids


@patch('pyinaturalist.client.client.get_access_token', return_value='token')
def test_delete_observations(get_access_token, requests_mock):
    requests_mock.post(
        f'{API_V2}/observations',
        json={
            'total_results': 1,
            'results': [
                {
                    'uuid': OBS_UUID,
                    'project_observations': [
                        {'id': 2, 'uuid': PROJECT_OBS_UUID, 'project': {'id': 1234}},
                    ],
                }
            ],
        },
        status_code=200,
    )
    requests_mock.delete(f'{API_V2}/project_observations/{PROJECT_OBS_UUID}', status_code=200)

    iNatClient().projects.delete_observations(1234, OBS_UUID)
    get_access_token.assert_called()

    delete_request = requests_mock.request_history[-1]
    assert delete_request.method == 'DELETE'
    assert delete_request.url == f'{API_V2}/project_observations/{PROJECT_OBS_UUID}'


# TODO:
# def test_update():
#     results = iNatClient().projects.update()


# def test_add_users():
#     results = iNatClient().project.add_users()


# def test_delete_users():
#     results = iNatClient().project.delete_users()
