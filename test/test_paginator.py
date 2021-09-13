import pytest

from pyinaturalist.constants import API_V1_BASE_URL
from pyinaturalist.models import Observation
from pyinaturalist.paginator import Paginator
from pyinaturalist.v1 import get_observations
from test.sample_data import SAMPLE_DATA


def test_iter(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations',
        [
            {'json': SAMPLE_DATA['get_observations_node_page1'], 'status_code': 200},
            {'json': SAMPLE_DATA['get_observations_node_page2'], 'status_code': 200},
        ],
    )

    paginator = Paginator(get_observations, Observation, id=[57754375, 57707611])
    observations = list(paginator)
    assert len(observations) == 2


def test_iter__with_limit(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations',
        [
            {'json': SAMPLE_DATA['get_observations_node_page1'], 'status_code': 200},
            {'json': SAMPLE_DATA['get_observations_node_page2'], 'status_code': 200},
        ],
    )

    paginator = Paginator(get_observations, Observation, id=[57754375, 57707611], limit=1)
    observations = list(paginator)
    assert len(observations) == 1


@pytest.mark.asyncio
async def test_async_iter(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations',
        [
            {'json': SAMPLE_DATA['get_observations_node_page1'], 'status_code': 200},
            {'json': SAMPLE_DATA['get_observations_node_page2'], 'status_code': 200},
        ],
    )

    paginator = Paginator(get_observations, Observation, id=[57754375, 57707611], page='all')
    observations = [obs async for obs in paginator]
    assert len(observations) == 2


def test_count(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations?per_page=0', json={'results': [], 'total_results': 50}
    )

    paginator = Paginator(get_observations, Observation, q='asdf')
    assert paginator.count() == 50
    assert paginator.total_results == 50


def test_next_page__exhausted():
    paginator = Paginator(get_observations, Observation)
    paginator.exhausted = True
    assert paginator.next_page() == []


def test_str():
    def get_observations(**kwargs):
        return {'total_results': 0}

    paginator = Paginator(get_observations, Observation)
    assert 'get_observations' in str(paginator)
    assert '0/unknown' in str(paginator)

    paginator.total_results = 50
    assert '0/50' in str(paginator)
