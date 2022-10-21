from asyncio import get_event_loop
from copy import deepcopy
from unittest.mock import patch

import pytest

from pyinaturalist.constants import API_V1
from pyinaturalist.models import Observation
from pyinaturalist.paginator import Paginator, WrapperPaginator
from pyinaturalist.v1 import get_observations
from test.sample_data import SAMPLE_DATA


def test_iter(requests_mock):
    page_1 = deepcopy(SAMPLE_DATA['get_observations_node_page1'])
    page_1['total_results'] = 3
    requests_mock.get(
        f'{API_V1}/observations',
        [
            {'json': page_1, 'status_code': 200},
            {'json': page_1, 'status_code': 200},
            {'json': page_1, 'status_code': 200},
            {'json': page_1, 'status_code': 200},
        ],
    )

    # Only 3 pages should be requested
    paginator = Paginator(get_observations, Observation, id=[57754375, 57707611], per_page=1)
    observations = list(paginator)
    assert paginator.page == 3
    assert len(observations) == 3


def test_iter__with_limit(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations',
        [
            {'json': SAMPLE_DATA['get_observations_node_page1'], 'status_code': 200},
            {'json': SAMPLE_DATA['get_observations_node_page2'], 'status_code': 200},
        ],
    )

    paginator = Paginator(get_observations, Observation, id=[57754375, 57707611], limit=1)
    observations = list(paginator)
    assert len(observations) == 1
    assert paginator.page == 1


@pytest.mark.asyncio
async def test_async_iter(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations',
        [
            {'json': SAMPLE_DATA['get_observations_node_page1'], 'status_code': 200},
            {'json': SAMPLE_DATA['get_observations_node_page2'], 'status_code': 200},
        ],
    )

    paginator = Paginator(
        get_observations,
        Observation,
        id=[57754375, 57707611],
        per_page=1,
        page='all',
    )
    observations = [obs async for obs in paginator]
    assert len(observations) == 2


@pytest.mark.asyncio
@patch('pyinaturalist.paginator.get_running_loop')
async def test_async_iter__custom_loop(mock_get_running_loop, requests_mock):
    """If an async event loop is specified, make sure that is used instead of the default loop"""
    requests_mock.get(
        f'{API_V1}/observations',
        [
            {'json': SAMPLE_DATA['get_observations_node_page1'], 'status_code': 200},
            {'json': SAMPLE_DATA['get_observations_node_page2'], 'status_code': 200},
        ],
    )

    paginator = Paginator(
        get_observations,
        Observation,
        id=[57754375, 57707611],
        per_page=1,
        page='all',
        loop=get_event_loop(),
    )
    observations = [obs async for obs in paginator]
    assert len(observations) == 2
    mock_get_running_loop.run_in_executor.assert_not_called()


@pytest.mark.asyncio
async def test_async_all(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations',
        [
            {'json': SAMPLE_DATA['get_observations_node_page1'], 'status_code': 200},
            {'json': SAMPLE_DATA['get_observations_node_page2'], 'status_code': 200},
        ],
    )

    paginator = Paginator(
        get_observations,
        Observation,
        id=[57754375, 57707611],
        per_page=1,
        page='all',
    )
    observations = await paginator.async_all()
    assert len(observations) == 2


def test_count(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations?per_page=0', json={'results': [], 'total_results': 50}
    )

    paginator = Paginator(get_observations, Observation, q='asdf')
    assert paginator.count() == 50

    # Subsequent calls should use the previously saved value
    assert paginator.count() == paginator.total_results == 50


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


def test_wrapper_paginator():
    results = [Observation(id=i) for i in range(10)]
    paginator = WrapperPaginator(results)
    paged_results = paginator.all()
    assert len(paged_results) == paginator.count() == 10
    assert paginator.exhausted is True
    assert paginator.all() == []
