import pytest

from pyinaturalist.constants import API_V1
from pyinaturalist.v1 import get_places_autocomplete, get_places_by_id, get_places_nearby
from test.sample_data import SAMPLE_DATA


def test_get_places_by_id(requests_mock):
    requests_mock.get(
        f'{API_V1}/places/93735,89191',
        json=SAMPLE_DATA['get_places_by_id'],
        status_code=200,
    )

    response = get_places_by_id([93735, 89191])
    result = response['results'][0]

    assert response['total_results'] == len(response['results']) == 2
    assert result['id'] == 93735
    assert result['name'] == 'Springbok'
    assert result['bbox_area'] == 0.000993854049
    assert result['location'] == [-29.665119, 17.88583]
    assert len(result['ancestor_place_ids']) == 4


@pytest.mark.parametrize('place_id', ['asdf', [None], [1, 'not a number']])
def test_get_places_by_id__invalid_inputs(place_id):
    with pytest.raises(ValueError):
        get_places_by_id(place_id)


def test_get_places_nearby(requests_mock):
    requests_mock.get(
        f'{API_V1}/places/nearby',
        json=SAMPLE_DATA['get_places_nearby'],
        status_code=200,
    )

    response = get_places_nearby(nelat=150.0, nelng=-50.0, swlat=-149.999, swlng=-49.999)
    result = response['results']['standard'][0]

    assert len(response['results']['standard']) + len(response['results']['community']) == 6

    assert result['id'] == 97394
    assert result['admin_level'] == -1
    assert result['name'] == 'North America'
    assert result['bbox_area'] == 28171.40875125
    assert result['location'] == [56.7732555574, -179.68825]
    assert result['ancestor_place_ids'] is None


def test_get_places_autocomplete(requests_mock):
    requests_mock.get(
        f'{API_V1}/places/autocomplete',
        json=SAMPLE_DATA['get_places_autocomplete'],
        status_code=200,
    )

    response = get_places_autocomplete('springbok')
    result = response['results'][0]

    assert response['total_results'] == len(response['results']) == 1
    assert result['id'] == 93735
    assert result['name'] == 'Springbok'
    assert result['bbox_area'] == 0.000993854049
    assert result['location'] == [-29.665119, 17.88583]
    assert len(result['ancestor_place_ids']) == 4


def test_get_places_autocomplete__all_pages(requests_mock):
    page_1 = {'total_results': 25, 'results': [{'id': i} for i in range(20)]}
    page_2 = {'total_results': 25, 'results': [{'id': i} for i in range(15, 25)]}
    requests_mock.get(
        f'{API_V1}/places/autocomplete',
        [
            {'json': page_1, 'status_code': 200},
            {'json': page_2, 'status_code': 200},
        ],
    )

    # Expect 2 requests, and for results to be deduplicated
    response = get_places_autocomplete('springbok', page='all')
    results = response['results']
    assert len(results) == 25


def test_get_places_autocomplete__single_page(requests_mock):
    page_1 = {'total_results': 20, 'results': [{'id': i} for i in range(20)]}
    page_2 = {'total_results': 20, 'results': [{'id': i} for i in range(15, 25)]}
    requests_mock.get(
        f'{API_V1}/places/autocomplete',
        [
            {'json': page_1, 'status_code': 200},
            {'json': page_2, 'status_code': 200},
        ],
    )

    # If all results are returned in the first request, expect just 1 request
    response = get_places_autocomplete('springbok', page='all')
    results = response['results']
    assert len(results) == 20
    assert max([r['id'] for r in results]) == 19
