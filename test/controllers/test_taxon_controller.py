from pyinaturalist.client import iNatClient
from pyinaturalist.constants import API_V1_BASE_URL
from pyinaturalist.models import Taxon
from test.sample_data import SAMPLE_DATA


def test_from_id(requests_mock):
    taxon_id = 70118
    requests_mock.get(
        f'{API_V1_BASE_URL}/taxa/{taxon_id}',
        json=SAMPLE_DATA['get_taxa_by_id'],
        status_code=200,
    )

    client = iNatClient()
    results = client.taxa.from_id(taxon_id).all()
    assert len(results) == 1 and isinstance(results[0], Taxon)
    assert results[0].id == taxon_id


def test_autocomplete(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/taxa/autocomplete',
        json=SAMPLE_DATA['get_taxa_autocomplete'],
        status_code=200,
    )

    client = iNatClient()
    results = client.taxa.autocomplete(q='vespi').all()
    assert len(results) == 10 and isinstance(results[0], Taxon)
    assert results[0].id == 52747


def test_search(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/taxa',
        json=SAMPLE_DATA['get_taxa'],
        status_code=200,
    )

    client = iNatClient()
    results = client.taxa.search(q='vespi', rank=['genus', 'subgenus', 'species']).all()
    assert len(results) == 30 and isinstance(results[0], Taxon)
    assert results[0].id == 70118
