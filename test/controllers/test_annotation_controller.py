import json
from unittest.mock import patch

from requests import Response

from pyinaturalist.client import iNatClient
from pyinaturalist.constants import API_V1, API_V2
from pyinaturalist.models import Annotation
from test.sample_data import SAMPLE_DATA, j_annotation_1


def test_all(requests_mock):
    requests_mock.get(
        f'{API_V1}/controlled_terms',
        json=SAMPLE_DATA['get_controlled_terms'],
        status_code=200,
    )
    terms = iNatClient().annotations.all()
    assert len(terms) == 4
    assert terms[0].id == 12
    assert terms[0].multivalued is True
    assert terms[0].label == 'Plant Phenology'
    assert len(terms[0].values) == 4
    assert terms[0].values[0].id == 21
    assert terms[0].values[0].label == 'No Evidence of Flowering'


def test_for_taxon(requests_mock):
    requests_mock.get(
        f'{API_V1}/controlled_terms/for_taxon',
        json=SAMPLE_DATA['get_controlled_terms_for_taxon'],
        status_code=200,
    )
    terms = iNatClient().annotations.for_taxon(47651)
    assert len(terms) == 1
    assert terms[0].id == 9


def test_lookup(requests_mock):
    requests_mock.get(
        f'{API_V1}/controlled_terms',
        json=SAMPLE_DATA['get_controlled_terms'],
        status_code=200,
    )
    requests_mock.get(
        f'{API_V1}/observations',
        json=SAMPLE_DATA['get_observation_with_ofvs'],
        status_code=200,
    )

    client = iNatClient()
    obs = client.observations.search().one()
    obs.annotations = client.annotations.lookup(obs.annotations)
    assert obs.annotations[0].controlled_attribute.label == 'Life Stage'
    assert obs.annotations[0].controlled_value.label == 'Adult'


@patch('pyinaturalist.controllers.annotation_controller.post')
def test_create(mock_post):
    response = Response()
    response._content = json.dumps({'results': [j_annotation_1]}).encode()
    mock_post.return_value = response

    client = iNatClient()
    result = client.annotations.create(
        controlled_attribute_id=12,
        controlled_value_id=13,
        resource_id=164609837,
    )
    assert isinstance(result, Annotation)

    request_params = mock_post.call_args[1]
    assert request_params['controlled_attribute_id'] == 12
    assert request_params['controlled_value_id'] == 13
    assert request_params['resource_id'] == 164609837
    assert request_params['resource_type'] == 'Observation'


@patch('pyinaturalist.controllers.annotation_controller.delete')
def test_delete(mock_delete):
    uuid = 'aad8ce8d-ed0a-4099-b21b-b03b9f51cad9'
    client = iNatClient()
    client.annotations.delete(uuid)
    mock_delete.assert_called_with(f'{API_V2}/annotations/{uuid}')
