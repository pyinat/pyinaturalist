# TODO: More thorough tests?
# Or are most relevant edge cases already covered by tests for v1.taxa?
from pyinaturalist.client import iNatClient
from pyinaturalist.constants import API_V1_BASE_URL
from pyinaturalist.models import Taxon
from test.conftest import load_sample_data


def test_from_id(requests_mock):
    taxon_id = 70118
    requests_mock.get(
        f'{API_V1_BASE_URL}/taxa/{taxon_id}',
        json=load_sample_data('get_taxa_by_id.json'),
        status_code=200,
    )

    client = iNatClient()
    results = client.taxa.from_id(taxon_id)
    assert len(results) == 1 and isinstance(results[0], Taxon)
    assert results[0].id == taxon_id


def test_autocomplete(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/taxa/autocomplete',
        json=load_sample_data('get_taxa_autocomplete.json'),
        status_code=200,
    )

    client = iNatClient()
    results = client.taxa.autocomplete(q='vespi')
    assert len(results) == 10 and isinstance(results[0], Taxon)
    assert results[0].id == 52747


def test_search(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/taxa',
        json=load_sample_data('get_taxa.json'),
        status_code=200,
    )

    client = iNatClient()
    results = client.taxa.search(q='vespi', rank=['genus', 'subgenus', 'species'])
    assert len(results) == 30 and isinstance(results[0], Taxon)
    assert results[0].id == 70118
