from datetime import datetime

from dateutil.tz import tzutc
from requests_cache import DO_NOT_CACHE

from pyinaturalist.constants import API_V1
from pyinaturalist.v1 import get_current_user, get_user_by_id, get_users_autocomplete
from pyinaturalist.v1 import users as users_module
from test.sample_data import SAMPLE_DATA


def test_get_user_by_id(requests_mock):
    user_id = 1
    requests_mock.get(
        f'{API_V1}/users/{user_id}',
        json=SAMPLE_DATA['get_user_by_id'],
        status_code=200,
    )

    user = get_user_by_id(user_id)
    assert user['id'] == user_id
    assert user['created_at'] == datetime(2008, 3, 20, 21, 15, 42, tzinfo=tzutc())
    assert user['spam'] is False


def test_get_users_autocomplete(requests_mock):
    requests_mock.get(
        f'{API_V1}/users/autocomplete',
        json=SAMPLE_DATA['get_users_autocomplete'],
        status_code=200,
    )

    response = get_users_autocomplete(q='niconoe')
    first_result = response['results'][0]

    assert len(response['results']) == response['total_results'] == 3
    assert first_result['id'] == 886482
    assert first_result['login'] == 'niconoe'
    assert first_result['created_at'] == datetime(2018, 4, 23, 17, 11, 14, tzinfo=tzutc())


def test_get_current_user(requests_mock):
    requests_mock.get(
        f'{API_V1}/users/me',
        json=SAMPLE_DATA['get_users_autocomplete'],
        status_code=200,
    )

    user = get_current_user()
    assert user['id'] == 886482
    assert user['login'] == 'niconoe'
    assert user['created_at'] == datetime(2018, 4, 23, 17, 11, 14, tzinfo=tzutc())


def test_get_current_user__disables_cache_by_default(monkeypatch):
    captured_kwargs = {}

    def mock_get(*_, **kwargs):
        captured_kwargs.update(kwargs)

        class _Response:
            @staticmethod
            def json():
                return SAMPLE_DATA['get_users_autocomplete']

        return _Response()

    monkeypatch.setattr(users_module, 'get', mock_get)
    users_module.get_current_user(access_token='test-token')

    assert captured_kwargs['force_refresh'] is True
    assert captured_kwargs['expire_after'] == DO_NOT_CACHE


def test_get_current_user__cache_settings_can_be_overridden(monkeypatch):
    captured_kwargs = {}

    def mock_get(*_, **kwargs):
        captured_kwargs.update(kwargs)

        class _Response:
            @staticmethod
            def json():
                return SAMPLE_DATA['get_users_autocomplete']

        return _Response()

    monkeypatch.setattr(users_module, 'get', mock_get)
    users_module.get_current_user(force_refresh=False, expire_after=300)

    assert captured_kwargs['force_refresh'] is False
    assert captured_kwargs['expire_after'] == 300
