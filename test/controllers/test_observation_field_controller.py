from pyinaturalist.client import iNatClient
from pyinaturalist.constants import API_V0, API_V1
from pyinaturalist.models import ObservationField
from test.sample_data import SAMPLE_DATA


def test_search(requests_mock):
    requests_mock.get(
        f'{API_V0}/observation_fields.json',
        json=SAMPLE_DATA['get_observation_fields_page1'],
        status_code=200,
    )
    fields = iNatClient().observation_fields.search(q='sex')
    assert len(fields) == 30
    assert isinstance(fields[0], ObservationField)
    assert fields[0].id == 4813
    assert fields[0].name == 'Sex (deer/turkey)'
    assert fields[0].datatype == 'text'


def test_search__no_query(requests_mock):
    requests_mock.get(
        f'{API_V0}/observation_fields.json',
        json=SAMPLE_DATA['get_observation_fields_page1'],
        status_code=200,
    )
    fields = iNatClient().observation_fields.search()
    assert len(fields) == 30


def test_set(requests_mock):
    requests_mock.post(
        f'{API_V1}/observation_field_values',
        json=SAMPLE_DATA['post_put_observation_field_value'],
        status_code=200,
    )
    response = iNatClient().observation_fields.set(
        observation_id=18166477,
        observation_field_id=31,
        value='fouraging',
        access_token='token',
    )
    assert response['id'] == 31
    assert response['observation_field_id'] == 31
    assert response['observation_id'] == 18166477
    assert response['value'] == 'fouraging'


def test_delete(requests_mock):
    requests_mock.delete(
        f'{API_V1}/observation_field_values/1234',
        json={'errors': []},
        status_code=200,
    )
    iNatClient().observation_fields.delete(1234, access_token='token')
