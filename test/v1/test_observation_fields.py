from pyinaturalist.constants import API_V1
from pyinaturalist.v1 import delete_observation_field, set_observation_field
from test.sample_data import SAMPLE_DATA


def test_set_observation_field(requests_mock):
    requests_mock.post(
        f'{API_V1}/observation_field_values',
        json=SAMPLE_DATA['post_put_observation_field_value'],
        status_code=200,
    )

    response = set_observation_field(
        observation_id=18166477,
        observation_field_id=31,  # Animal behavior
        value='fouraging',
        access_token='token',
    )

    assert response['id'] == 31
    assert response['observation_field_id'] == 31
    assert response['observation_id'] == 18166477
    assert response['value'] == 'fouraging'


def test_delete_observation_field(requests_mock):
    requests_mock.delete(
        f'{API_V1}/observation_field_values/1234',
        json={'errors': []},
        status_code=200,
    )
    response = delete_observation_field(1234)
    assert response['errors'] == []
