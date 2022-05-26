from datetime import datetime

from dateutil.tz import tzutc

from pyinaturalist.constants import API_V1
from pyinaturalist.v1 import get_posts
from test.conftest import load_sample_data


def test_get_posts_from_login(requests_mock):
    requests_mock.get(
        f'{API_V1}/posts?login=eduramirezh',
        json=load_sample_data('get_posts_login.json'),
        status_code=200,
    )

    posts = get_posts(login='eduramirezh')

    first_result = posts[0]

    assert len(posts) == 3
    assert first_result['parent_id'] == 3986099
    assert first_result['created_at'] == datetime(2021, 7, 2, 20, 55, 31, 340000, tzinfo=tzutc())


def test_get_posts_from_project(requests_mock):
    requests_mock.get(
        f'{API_V1}/posts?project_id=100',
        json=load_sample_data('get_posts_project.json'),
        status_code=200,
    )

    posts = get_posts(project_id=100)

    first_result = posts[0]

    assert len(posts) == 10
    assert first_result['parent_id'] == 100
    assert first_result['created_at'] == datetime(2021, 3, 6, 12, 57, 2, 902000, tzinfo=tzutc())
