import json
from unittest.mock import patch

import pytest

from pyinaturalist.constants import API_V2
from pyinaturalist.v2 import get_taxa, get_taxa_autocomplete, get_taxa_by_id, get_taxa_iconic
from test.sample_data import SAMPLE_DATA

CLASS_AND_HIGHER = ['class', 'superclass', 'subphylum', 'phylum', 'kingdom']
SPECIES_AND_LOWER = ['infrahybrid', 'form', 'variety', 'subspecies', 'hybrid', 'species']
CLASS_THOUGH_PHYLUM = ['class', 'superclass', 'subphylum', 'phylum']


def test_get_taxa__minimal(requests_mock):
    requests_mock.get(
        f'{API_V2}/taxa',
        json=SAMPLE_DATA['get_taxa_minimal'],
        status_code=200,
    )

    taxa = get_taxa(q='vespi')
    assert taxa['total_results'] == 65
    assert taxa['results'][0]['id'] == 52747


def test_get_taxa__all_fields(requests_mock):
    requests_mock.get(
        f'{API_V2}/taxa',
        json=SAMPLE_DATA['get_taxa_full'],
        status_code=200,
    )

    taxa = get_taxa(q='vespi', fields='all')
    assert taxa['results'][0]['id'] == 52747
    assert taxa['results'][0]['name'] == 'Vespidae'
    assert len(taxa['results'][0].keys()) == 24


def test_get_taxa__some_fields(requests_mock):
    requests_mock.post(
        f'{API_V2}/taxa',
        json=SAMPLE_DATA['get_taxa_full'],
        status_code=200,
    )

    taxa = get_taxa(q='vespi', fields={'name': True, 'rank': True})
    assert taxa['results'][0]['id'] == 52747
    assert taxa['results'][0]['name'] == 'Vespidae'


@patch('pyinaturalist.session.format_response')
@patch('requests.sessions.Session.send')
def test_get_taxa__except_fields(mock_send, mock_format):
    get_taxa(q='vespi', except_fields=['default_photo'])
    request_obj = mock_send.call_args[0][0]
    json_body = json.loads(request_obj.body.decode())
    assert 'default_photo' not in json_body['fields']
    assert 'name' in json_body['fields']


def test_get_taxa__invalid_fields():
    with pytest.raises(ValueError):
        get_taxa(q='vespi', fields=['name'], except_fields=['default_photo'])


def test_get_taxa__all_pages(requests_mock):
    requests_mock.get(
        f'{API_V2}/taxa',
        [
            {'json': SAMPLE_DATA['get_taxa_minimal'], 'status_code': 200},
            {'json': {**SAMPLE_DATA['get_taxa_minimal'], 'results': []}, 'status_code': 200},
        ],
    )

    taxa = get_taxa(q='vespi', page='all')
    assert len(taxa['results']) == 30


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
@patch('pyinaturalist.v2.taxa.get')
def test_get_taxa_by_rank_range(mock_get, params, expected_ranks):
    # Make sure custom rank params result in the correct 'rank' param value
    get_taxa(**params)
    call_params = mock_get.call_args[1]
    requested_rank = call_params['rank']
    assert requested_rank == expected_ranks


def test_get_taxa_by_id__minimal(requests_mock):
    requests_mock.get(
        f'{API_V2}/taxa/70118',
        json=SAMPLE_DATA['get_taxa_by_id_minimal'],
        status_code=200,
    )

    taxa = get_taxa_by_id(70118)
    assert taxa['total_results'] == 1
    assert taxa['results'][0]['id'] == 70118


def test_get_taxa_by_id__all_fields(requests_mock):
    requests_mock.get(
        f'{API_V2}/taxa/70118',
        json=SAMPLE_DATA['get_taxa_by_id_full'],
        status_code=200,
    )

    taxa = get_taxa_by_id(70118, fields='all')
    assert taxa['results'][0]['id'] == 70118
    assert taxa['results'][0]['name'] == 'Nicrophorus vespilloides'


def test_get_taxa_autocomplete(requests_mock):
    requests_mock.get(
        f'{API_V2}/taxa/autocomplete',
        json=SAMPLE_DATA['get_taxa_minimal'],
        status_code=200,
    )

    taxa = get_taxa_autocomplete(q='vespi')
    assert taxa['total_results'] == 65
    assert taxa['results'][0]['id'] == 52747


def test_get_taxa_iconic(requests_mock):
    requests_mock.get(
        f'{API_V2}/taxa/iconic',
        json=SAMPLE_DATA['get_taxa_iconic_full'],
        status_code=200,
    )

    taxa = get_taxa_iconic(fields='all')
    assert taxa['total_results'] == 13
    assert taxa['results'][0]['id'] == 1
    assert taxa['results'][0]['name'] == 'Animalia'
