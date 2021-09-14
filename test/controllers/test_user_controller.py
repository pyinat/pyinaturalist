from pyinaturalist.client import iNatClient
from pyinaturalist.constants import API_V1_BASE_URL
from pyinaturalist.models import User
from test.sample_data import SAMPLE_DATA


def test_from_id__one(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/users/1',
        json=SAMPLE_DATA['get_user_by_id'],
        status_code=200,
    )

    client = iNatClient()
    result = client.users.from_id(1).one()
    assert isinstance(result, User)
    assert result.id == 1


def test_from_id__multiple(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/users/1',
        json=SAMPLE_DATA['get_user_by_id'],
        status_code=200,
    )
    requests_mock.get(
        f'{API_V1_BASE_URL}/users/2',
        json=SAMPLE_DATA['get_user_by_id'],
        status_code=200,
    )

    client = iNatClient()
    results = client.users.from_id(1, 2).all()
    assert len(results) == 2 and isinstance(results[0], User)
    assert results[0].id == 1


def test_autocomplete(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/users/autocomplete',
        json=SAMPLE_DATA['get_users_autocomplete'],
        status_code=200,
    )

    client = iNatClient()
    results = client.users.autocomplete(q='nico')
    assert len(results) == 3 and isinstance(results[0], User)
    assert results[0].id == 886482
