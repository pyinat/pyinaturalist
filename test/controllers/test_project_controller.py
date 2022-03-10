# flake8: noqa: F405
from datetime import datetime
from unittest.mock import patch

from dateutil.tz import tzutc

from pyinaturalist.client import iNatClient
from pyinaturalist.constants import API_V1_BASE_URL
from pyinaturalist.models import Project, ProjectObservationField, ProjectUser, User
from test.sample_data import SAMPLE_DATA, j_project_1, j_project_2, j_project_3_obs_fields


def test_from_id(requests_mock):
    project_id = 8291
    requests_mock.get(
        f'{API_V1_BASE_URL}/projects/{project_id}',
        json={'results': [j_project_1, j_project_2], 'total_results': 2},
        status_code=200,
    )
    client = iNatClient()
    results = client.projects.from_id(project_id).all()
    project = results[0]
    assert len(results) == 2 and isinstance(project, Project)

    assert project.id == project_id
    assert project.location == (48.777404, -122.306929)
    assert project.project_observation_rules == project.obs_rules
    assert project.obs_rules[0]['id'] == 19344
    assert project.search_parameters[0]['field'] == 'quality_grade'
    assert project.user_ids[-1] == 3387092 and len(project.user_ids) == 33

    admin = project.admins[0]
    assert isinstance(admin, ProjectUser) and admin.id == 233188 and admin.role == 'manager'
    assert isinstance(project.user, User) and project.user.id == 233188


def test_search(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/projects',
        json=SAMPLE_DATA['get_projects'],
        status_code=200,
    )
    client = iNatClient()
    results = client.projects.search(
        q='invasive',
        lat=49.27,
        lng=-123.08,
        radius=400,
        order_by='distance',
    ).all()

    project = results[0]
    assert len(results) == 5 and isinstance(project, Project)
    assert project.id == 8291
    assert project.title == 'PNW Invasive Plant EDDR'
    assert project.is_umbrella is False
    assert len(project.user_ids) == 33
    assert project.created_at == datetime(2016, 7, 20, 23, 0, 5, tzinfo=tzutc())
    assert project.updated_at == datetime(2020, 7, 28, 20, 9, 49, tzinfo=tzutc())


def test_search__with_obs_fields(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/projects',
        json={'results': [j_project_3_obs_fields], 'total_results': 1},
        status_code=200,
    )
    client = iNatClient()
    results = client.projects.search(id=1234).all()
    obs_field = results[0].project_observation_fields[0]

    assert isinstance(obs_field, ProjectObservationField)
    assert obs_field.id == 30
    assert obs_field.position == 0
    assert obs_field.required is False


@patch('pyinaturalist.client.get_access_token', return_value='token')
def test_add_observation(get_access_token, requests_mock):
    requests_mock.post(
        f'{API_V1_BASE_URL}/project_observations',
        json=SAMPLE_DATA['add_project_observation'],
        status_code=200,
    )
    client = iNatClient()
    observation_ids = 5678, 9012
    client.projects.add_observations(1234, *observation_ids)
    get_access_token.assert_called_once()
