from datetime import datetime

from dateutil.tz import tzoffset

from pyinaturalist.constants import API_V1
from pyinaturalist.v1 import get_message_by_id, get_messages, get_unread_meassage_count
from test.sample_data import SAMPLE_DATA


def test_get_message_by_id(requests_mock):
    message_id = 12345
    requests_mock.get(
        f'{API_V1}/messages/{message_id}',
        json=SAMPLE_DATA['get_messages'],
        status_code=200,
    )

    message = get_message_by_id(message_id)['results'][0]
    assert message['id'] == message_id
    assert message['created_at'] == datetime(
        2019, 9, 2, 18, 50, 24, 651000, tzinfo=tzoffset(None, -18000)
    )
    assert message['from_user']['id'] == 12345
    assert message['to_user']['id'] == 2115051


def test_get_messages(requests_mock):
    requests_mock.get(
        f'{API_V1}/messages',
        json=SAMPLE_DATA['get_messages'],
        status_code=200,
    )

    message = get_messages()['results'][0]
    assert message['id'] == 12345
    assert message['created_at'] == datetime(
        2019, 9, 2, 18, 50, 24, 651000, tzinfo=tzoffset(None, -18000)
    )
    assert message['from_user']['id'] == 12345
    assert message['to_user']['id'] == 2115051


def test_get_messages__threads(requests_mock):
    requests_mock.get(
        f'{API_V1}/messages',
        json=SAMPLE_DATA['get_messages'],
        status_code=200,
    )

    message = get_messages(threads=True)['results'][0]
    assert message['id'] == 12345


def test_get_unread_meassage_count(requests_mock):
    requests_mock.get(
        f'{API_V1}/messages/unread',
        json={'count': 12},
        status_code=200,
    )

    assert get_unread_meassage_count() == 12


def test_get_unread_meassage_count__invalid(requests_mock):
    requests_mock.get(
        f'{API_V1}/messages/unread',
        json={'results': 'invalid'},
        status_code=200,
    )

    assert get_unread_meassage_count() == 0
