from copy import deepcopy

import pytest

from pyinaturalist.client import iNatClient
from pyinaturalist.constants import API_V1
from pyinaturalist.models import Taxon
from pyinaturalist.paginator import Paginator, WrapperPaginator
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

    results = iNatClient().taxa.autocomplete(q='vespi')
    assert isinstance(results, Paginator)
    assert not isinstance(results, WrapperPaginator)
    all_results = results.all()
    assert len(all_results) == 10 and isinstance(all_results[0], Taxon)
    assert all_results[0].id == 52747


def test_autocomplete__full_records(requests_mock):
    autocomplete_results = deepcopy(SAMPLE_DATA['get_taxa_autocomplete'])
    autocomplete_results['results'] = [autocomplete_results['results'][0]]
    autocomplete_results['total_results'] = 1
    autocomplete_results['per_page'] = 1

    full_taxon = deepcopy(SAMPLE_DATA['get_taxa_by_id'])
    full_taxon['results'][0]['id'] = 52747
    full_taxon['results'][0].pop('matched_term', None)

    requests_mock.get(
        f'{API_V1}/taxa/autocomplete',
        json=autocomplete_results,
        status_code=200,
    )
    requests_mock.get(
        f'{API_V1}/taxa/52747',
        json=full_taxon,
        status_code=200,
    )

    taxon = iNatClient().taxa.autocomplete(q='vespi', full_records=True).one()
    assert isinstance(taxon, Taxon)
    assert taxon.id == 52747
    assert taxon.matched_term == 'Vespidae'
    assert len(taxon.ancestors) > 0


def test_autocomplete__full_records__empty_results(requests_mock):
    requests_mock.get(
        f'{API_V1}/taxa/autocomplete',
        json={'results': [], 'total_results': 0, 'per_page': 0},
        status_code=200,
    )

    results = iNatClient().taxa.autocomplete(q='raven', full_records=True).all()
    assert results == []


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
    assert len(taxon.ancestors) == 13
