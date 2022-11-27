from pyinaturalist.client import iNatClient
from pyinaturalist.constants import API_V1
from test.sample_data import SAMPLE_DATA


def test_all(requests_mock):
    requests_mock.get(
        f'{API_V1}/controlled_terms',
        json=SAMPLE_DATA['get_controlled_terms'],
        status_code=200,
    )
    terms = iNatClient().controlled_terms.all()
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
    terms = iNatClient().controlled_terms.for_taxon(47651)
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
    obs.annotations = client.controlled_terms.lookup(obs.annotations)
    assert obs.annotations[0].controlled_attribute.label == 'Life Stage'
    assert obs.annotations[0].controlled_value.label == 'Adult'
