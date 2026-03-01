import pytest

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
    assert len(terms) == 7
    assert terms[0].id == 17
    assert terms[0].multivalued is False
    assert terms[0].label == 'Alive or Dead'
    assert len(terms[0].values) == 3
    assert terms[0].values[0].id == 18
    assert terms[0].values[0].label == 'Alive'


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


def test_lookup__doesnt_exist(requests_mock):
    requests_mock.get(
        f'{API_V1}/controlled_terms',
        json=SAMPLE_DATA['get_controlled_terms'],
        status_code=200,
    )

    client = iNatClient()
    annotations = [Annotation(controlled_attribute_id=id) for id in [12, 999]]
    annotations = client.annotations.lookup(annotations)
    assert len(annotations) == 2
    assert annotations[0].term == 'Flowers and Fruits'
    assert annotations[1].term == '999'  # Unable to look up; use ID as placeholder


def test_create(requests_mock):
    requests_mock.post(
        f'{API_V2}/annotations',
        json={'results': [j_annotation_1]},
        status_code=200,
    )

    client = iNatClient()
    result = client.annotations.create(
        164609837,
        controlled_attribute_id=12,
        controlled_value_id=13,
    )
    assert isinstance(result, Annotation)

    request = requests_mock.request_history[0]
    assert request.qs['controlled_attribute_id'] == ['12']
    assert request.qs['controlled_value_id'] == ['13']
    assert request.qs['resource_id'] == ['164609837']
    assert request.qs['resource_type'] == ['observation']


def test_create__by_label(requests_mock):
    requests_mock.get(
        f'{API_V1}/controlled_terms',
        json=SAMPLE_DATA['get_controlled_terms'],
        status_code=200,
    )
    requests_mock.post(
        f'{API_V2}/annotations',
        json={'results': [j_annotation_1]},
        status_code=200,
    )

    client = iNatClient()
    result = client.annotations.create(
        164609837,
        term='Alive or Dead',
        value='Alive',
    )
    assert isinstance(result, Annotation)

    request = requests_mock.request_history[-1]
    assert request.qs['controlled_attribute_id'] == ['17']
    assert request.qs['controlled_value_id'] == ['18']
    assert request.qs['resource_id'] == ['164609837']


def test_create__missing_term_value_pair():
    with pytest.raises(ValueError, match='Must specify either'):
        iNatClient().annotations.create(164609837, term='Alive or Dead')


def test_create__missing_resource_id():
    with pytest.raises(TypeError, match='resource_id'):
        iNatClient().annotations.create(term='Alive or Dead', value='Alive')


def test_create__invalid_term(requests_mock):
    requests_mock.get(
        f'{API_V1}/controlled_terms',
        json=SAMPLE_DATA['get_controlled_terms'],
        status_code=200,
    )
    with pytest.raises(ValueError, match='Annotation term not found'):
        iNatClient().annotations.create(164609837, term='Not a term', value='Alive')


def test_create__invalid_value_for_term(requests_mock):
    requests_mock.get(
        f'{API_V1}/controlled_terms',
        json=SAMPLE_DATA['get_controlled_terms'],
        status_code=200,
    )
    with pytest.raises(ValueError, match='Annotation value not found for term'):
        iNatClient().annotations.create(
            164609837,
            term='Alive or Dead',
            value='Not a value',
        )


def test_delete(requests_mock):
    uuid = 'aad8ce8d-ed0a-4099-b21b-b03b9f51cad9'
    requests_mock.delete(f'{API_V2}/annotations/{uuid}', status_code=200)
    iNatClient().annotations.delete(uuid)
    assert requests_mock.called
