from copy import deepcopy

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


def test_taxon__populate(requests_mock):
    full_taxon = deepcopy(SAMPLE_DATA['get_taxa_by_id'])
    full_taxon['results'][0]['conservation_status'] = {'authority': 'IUCN', 'status': 'LC'}
    requests_mock.get(
        f'{API_V1}/taxa/343248',
        json=full_taxon,
        status_code=200,
    )
    taxon = Taxon(
        id=343248,
        matched_term='nicroph',
        names=[{'name': 'Nicrophorus vespilloides'}],
    )
    taxon = iNatClient().taxa.populate(taxon)

    assert taxon.name == 'Nicrophorus vespilloides'
    # matched_term (from autocomplete) and names (from all_names) should not be overwritten
    assert taxon.matched_term == 'nicroph'
    assert taxon.names[0]['name'] == 'Nicrophorus vespilloides'
    assert taxon.conservation_status.authority == 'IUCN'
    assert len(taxon.ancestors) == 12
