from datetime import datetime
from unittest.mock import patch

from dateutil.tz import tzutc

from pyinaturalist.client import iNatClient
from pyinaturalist.constants import API_V1
from pyinaturalist.models import User
from test.sample_data import SAMPLE_DATA


def test_from_id(requests_mock):
    requests_mock.get(
        f'{API_V1}/users/1',
        json=SAMPLE_DATA['get_user_by_id'],
        status_code=200,
    )

    result = iNatClient().users(1)
    assert isinstance(result, User)
    assert result.id == 1


def test_from_ids(requests_mock):
    requests_mock.get(
        f'{API_V1}/users/1',
        json=SAMPLE_DATA['get_user_by_id'],
        status_code=200,
    )
    requests_mock.get(
        f'{API_V1}/users/2',
        json=SAMPLE_DATA['get_user_by_id'],
        status_code=200,
    )

    results = iNatClient().users.from_ids([1, 2]).all()
    assert len(results) == 2 and isinstance(results[0], User)
    assert results[0].id == 1


def test_autocomplete(requests_mock):
    requests_mock.get(
        f'{API_V1}/users/autocomplete',
        json=SAMPLE_DATA['get_users_autocomplete'],
        status_code=200,
    )

    results = iNatClient().users.autocomplete(q='nico')
    assert len(results) == 3 and isinstance(results[0], User)
    assert results[0].id == 886482


@patch('pyinaturalist.client.get_access_token', return_value='token')
def test_me(get_access_token, requests_mock):
    requests_mock.get(
        f'{API_V1}/users/me',
        json=SAMPLE_DATA['get_users_autocomplete'],
        status_code=200,
    )

    user = iNatClient().users.me()
    assert user.id == 886482
    assert user.login == 'niconoe'
    assert user.created_at == datetime(2018, 4, 23, 17, 11, 14, tzinfo=tzutc())
