from datetime import datetime

from dateutil.tz import tzoffset

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


def test_search(requests_mock):
    requests_mock.get(
        f'{API_V1}/identifications',
        json=SAMPLE_DATA['get_identifications'],
        status_code=200,
    )
    results = iNatClient().identifications.search().all()
    assert len(results) == 2
    expected_datetime = datetime(2021, 2, 18, 20, 31, 32, tzinfo=tzoffset(None, -21600))

    assert results[0].id == 155554373
    assert results[0].user.id == 2115051
    assert results[0].taxon.id == 60132
    assert results[0].created_at == expected_datetime
    assert results[0].current is True
