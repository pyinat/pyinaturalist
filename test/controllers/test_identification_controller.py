from pyinaturalist.client import iNatClient
from pyinaturalist.constants import API_V1
from pyinaturalist.models import (
    Identification,
)
from test.sample_data import SAMPLE_DATA


def test_from_id(requests_mock):
    identification_id = 700305837
    requests_mock.get(
        f'{API_V1}/identifications/{identification_id}',
        json=SAMPLE_DATA['get_identifications_by_id'],
        status_code=200,
    )
    result = iNatClient().identifications(identification_id)

    assert isinstance(result, Identification)
    assert result.id == identification_id


def test_from_id__not_found(requests_mock):
    identification_id = 16227955
    requests_mock.get(
        f'{API_V1}/identifications/{identification_id}',
        json={'results': [], 'total_results': 0},
        status_code=200,
    )
    assert iNatClient().identifications(identification_id) is None


def test_from_ids(requests_mock):
    identification_id = 700305837
    ids = SAMPLE_DATA['get_identifications_by_id']['results'][0]
    requests_mock.get(
        f'{API_V1}/identifications/{identification_id}',
        json={'results': [ids, ids], 'total_results': 2},
        status_code=200,
    )
    results = iNatClient().identifications.from_ids(identification_id).all()

    assert len(results) == 2 and isinstance(results[0], Identification)
    assert results[0].id == identification_id


def test_from_ids__limit(requests_mock):
    identification_id = 700305837
    requests_mock.get(
        f'{API_V1}/identifications/{identification_id}',
        [
            {'json': SAMPLE_DATA['get_identifications_by_id'], 'status_code': 200},
            {'json': SAMPLE_DATA['get_identifications_by_id'], 'status_code': 200},
        ],
    )
    results = iNatClient().identifications.from_ids(identification_id).limit(1)

    assert len(results) == 1 and isinstance(results[0], Identification)
    assert results[0].id == identification_id
