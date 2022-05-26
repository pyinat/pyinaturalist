from pyinaturalist.client import iNatClient
from pyinaturalist.constants import API_V1
from pyinaturalist.models import Taxon
from test.sample_data import SAMPLE_DATA


def test_from_id(requests_mock):
    taxon_id = 70118
    requests_mock.get(
        f'{API_V1}/taxa/{taxon_id}',
        json=SAMPLE_DATA['get_taxa_by_id'],
        status_code=200,
    )

    result = iNatClient().taxa(taxon_id)
    assert isinstance(result, Taxon)
    assert result.id == taxon_id


def test_from_ids(requests_mock):
    taxon_id = 70118
    requests_mock.get(
        f'{API_V1}/taxa/{taxon_id}',
        json=SAMPLE_DATA['get_taxa_by_id'],
        status_code=200,
    )

    results = iNatClient().taxa.from_ids(taxon_id).all()
    assert len(results) == 1 and isinstance(results[0], Taxon)
    assert results[0].id == taxon_id


def test_autocomplete(requests_mock):
    requests_mock.get(
        f'{API_V1}/taxa/autocomplete',
        json=SAMPLE_DATA['get_taxa_autocomplete'],
        status_code=200,
    )

    results = iNatClient().taxa.autocomplete(q='vespi').all()
    assert len(results) == 10 and isinstance(results[0], Taxon)
    assert results[0].id == 52747


def test_search(requests_mock):
    requests_mock.get(
        f'{API_V1}/taxa',
        json=SAMPLE_DATA['get_taxa'],
        status_code=200,
    )

    results = iNatClient().taxa.search(q='vespi', rank=['genus', 'subgenus', 'species']).all()
    assert len(results) == 30 and isinstance(results[0], Taxon)
    assert results[0].id == 70118
