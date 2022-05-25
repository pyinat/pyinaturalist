from unittest.mock import patch
from urllib.parse import urlencode

import pytest

from pyinaturalist.constants import API_V1
from pyinaturalist.v1 import get_taxa, get_taxa_autocomplete, get_taxa_by_id, get_taxa_map_layers
from test.conftest import load_sample_data

CLASS_AND_HIGHER = ['class', 'superclass', 'subphylum', 'phylum', 'kingdom']
SPECIES_AND_LOWER = ['form', 'variety', 'subspecies', 'hybrid', 'species']
CLASS_THOUGH_PHYLUM = ['class', 'superclass', 'subphylum', 'phylum']


def test_get_taxa(requests_mock):
    params = {'q': 'vespi', 'rank': 'genus,subgenus,species'}
    requests_mock.get(
        f'{API_V1}/taxa?{urlencode(params)}',
        json=load_sample_data('get_taxa.json'),
        status_code=200,
    )

    response = get_taxa(q='vespi', rank=['genus', 'subgenus', 'species'])
    first_result = response['results'][0]

    assert len(response['results']) == response['total_results'] == 30
    assert first_result['id'] == 70118
    assert first_result['name'] == 'Nicrophorus vespilloides'
    assert first_result['rank'] == 'species'
    assert first_result['is_active'] is True
    assert len(first_result['ancestor_ids']) == 14


@pytest.mark.parametrize(
    'params, expected_ranks',
    [
        ({'rank': 'genus'}, 'genus'),
        ({'min_rank': 'class'}, CLASS_AND_HIGHER),
        ({'max_rank': 'species'}, SPECIES_AND_LOWER),
        ({'min_rank': 'class', 'max_rank': 'phylum'}, CLASS_THOUGH_PHYLUM),
        ({'max_rank': 'species', 'rank': 'override_me'}, SPECIES_AND_LOWER),
    ],
)
@patch('pyinaturalist.v1.taxa.get')
def test_get_taxa_by_rank_range(
    mock_get,
    params,
    expected_ranks,
):
    # Make sure custom rank params result in the correct 'rank' param value
    get_taxa(**params)
    params = mock_get.call_args[1]
    requested_rank = params['rank']
    assert requested_rank == expected_ranks


def test_get_taxa_by_id(requests_mock):
    taxon_id = 70118
    requests_mock.get(
        f'{API_V1}/taxa/{taxon_id}',
        json=load_sample_data('get_taxa_by_id.json'),
        status_code=200,
    )

    response = get_taxa_by_id(taxon_id)
    result = response['results'][0]
    assert response['total_results'] == len(response['results']) == 1
    assert result['id'] == taxon_id
    assert result['name'] == 'Nicrophorus vespilloides'
    assert result['rank'] == 'species'
    assert result['is_active'] is True
    assert len(result['ancestors']) == 12


@pytest.mark.parametrize('taxon_id', ['asdf', [None], [1, 'not a number']])
def test_get_taxa_by_id__invalid_inputs(taxon_id):
    with pytest.raises(ValueError):
        get_taxa_by_id(taxon_id)


def test_get_taxa_autocomplete(requests_mock):
    requests_mock.get(
        f'{API_V1}/taxa/autocomplete',
        json=load_sample_data('get_taxa_autocomplete.json'),
        status_code=200,
    )

    response = get_taxa_autocomplete(q='vespi')
    first_result = response['results'][0]

    assert len(response['results']) == response['total_results'] == 10
    assert first_result['matched_term'] == 'Vespidae'
    assert first_result['id'] == 52747
    assert first_result['name'] == 'Vespidae'
    assert first_result['rank'] == 'family'
    assert first_result['is_active'] is True
    assert len(first_result['ancestor_ids']) == 11


def test_get_taxa_map_layers(requests_mock):
    requests_mock.get(
        f'{API_V1}/taxa/47588/map_layers',
        json=load_sample_data('get_taxa_map_layers.json'),
        status_code=200,
    )

    response = get_taxa_map_layers(47588)
    assert response['gbif_id'] == 2820380
    assert response['gbif_url'] == 'https://www.gbif.org/species/2820380'
    assert response['ranges'] is False
    assert response['listed_places'] is True
