import pytest
from unittest.mock import patch
from urllib.parse import urlencode

from pyinaturalist.constants import API_V1_BASE_URL
from pyinaturalist.v1 import get_taxa, get_taxa_autocomplete, get_taxa_by_id
from test.conftest import load_sample_data

CLASS_AND_HIGHER = ['class', 'superclass', 'subphylum', 'phylum', 'kingdom']
SPECIES_AND_LOWER = ['form', 'variety', 'subspecies', 'hybrid', 'species']
CLASS_THOUGH_PHYLUM = ['class', 'superclass', 'subphylum', 'phylum']


def test_get_taxa(requests_mock):
    params = {'q': 'vespi', 'rank': 'genus,subgenus,species'}
    requests_mock.get(
        f'{API_V1_BASE_URL}/taxa?{urlencode(params)}',
        json=load_sample_data('get_taxa.json'),
        status_code=200,
    )

    response = get_taxa(q='vespi', rank=['genus', 'subgenus', 'species'])
    first_result = response['results'][0]

    assert len(response['results']) == 30
    assert response['total_results'] == 35
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
@patch('pyinaturalist.v1.taxa.get_v1')
def test_get_taxa_by_rank_range(
    mock_get,
    params,
    expected_ranks,
):
    # Make sure custom rank params result in the correct 'rank' param value
    get_taxa(**params)
    kwargs = mock_get.call_args[1]
    requested_rank = kwargs['params']['rank']
    assert requested_rank == expected_ranks


# This is just a spot test of a case in which boolean params should be converted
@patch('pyinaturalist.api_requests.requests.Session.request')
def test_get_taxa_by_name_and_is_active(request):
    get_taxa(q='Lixus bardanae', is_active=False)
    request_kwargs = request.call_args[1]
    assert request_kwargs['params'] == {'q': 'Lixus bardanae', 'is_active': 'false'}


def test_get_taxa_by_id(requests_mock):
    taxon_id = 70118
    requests_mock.get(
        f'{API_V1_BASE_URL}/taxa/{taxon_id}',
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
        f'{API_V1_BASE_URL}/taxa/autocomplete',
        json=load_sample_data('get_taxa_autocomplete.json'),
        status_code=200,
    )

    response = get_taxa_autocomplete(q='vespi')
    first_result = response['results'][0]

    assert len(response['results']) == 10
    assert response['total_results'] == 47
    assert first_result['matched_term'] == 'Vespidae'
    assert first_result['id'] == 52747
    assert first_result['name'] == 'Vespidae'
    assert first_result['rank'] == 'family'
    assert first_result['is_active'] is True
    assert len(first_result['ancestor_ids']) == 11
