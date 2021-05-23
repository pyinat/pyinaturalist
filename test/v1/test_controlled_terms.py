from pyinaturalist.constants import API_V1_BASE_URL
from pyinaturalist.v1 import get_controlled_terms
from test.conftest import load_sample_data


def test_get_controlled_terms(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/controlled_terms',
        json=load_sample_data('get_controlled_terms.json'),
        status_code=200,
    )
    response = get_controlled_terms()
    assert len(response['results']) == 4
    first_result = response['results'][0]

    assert first_result['id'] == 12
    assert first_result['multivalued'] is True
    assert first_result['label'] == 'Plant Phenology'
    assert len(first_result['values']) == 4
    assert first_result['values'][0]
    assert first_result['values'][0]['id'] == 21
    assert first_result['values'][0]['label'] == 'No Evidence of Flowering'


def test_get_controlled_terms_for_taxon(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/controlled_terms/for_taxon',
        json=load_sample_data('get_controlled_terms_for_taxon.json'),
        status_code=200,
    )
    response = get_controlled_terms(47651)
    assert len(response['results']) == 1
    first_result = response['results'][0]

    assert first_result['id'] == 9
    assert first_result['multivalued'] is False
    assert first_result['label'] == 'Sex'
    assert len(first_result['values']) == 3
    assert first_result['values'][0]
    assert first_result['values'][0]['id'] == 10
    assert first_result['values'][0]['label'] == 'Female'
