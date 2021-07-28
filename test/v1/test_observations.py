from datetime import datetime
from unittest.mock import patch

import pytest
from dateutil.tz import tzoffset, tzutc

from pyinaturalist.constants import API_V1_BASE_URL
from pyinaturalist.exceptions import ObservationNotFound
from pyinaturalist.v1 import (
    get_observation,
    get_observation_histogram,
    get_observation_identifiers,
    get_observation_observers,
    get_observation_species_counts,
    get_observation_taxonomy,
    get_observations,
)
from test.conftest import load_sample_data


def test_get_observation(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations',
        json=load_sample_data('get_observation.json'),
        status_code=200,
    )

    observation = get_observation(16227955)
    assert observation['quality_grade'] == 'research'
    assert observation['id'] == 16227955
    assert observation['user']['login'] == 'niconoe'
    assert len(observation['photos']) == 2


def test_get_observation_histogram(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations/histogram',
        json=load_sample_data('get_observation_histogram_month.json'),
        status_code=200,
    )

    histogram = get_observation_histogram(
        interval='month', place_id=24, d1='2020-01-01', d2='2020-12-31'
    )
    assert len(histogram) == 12
    assert histogram[datetime(2020, 1, 1, 0, 0)] == 272
    assert all([isinstance(k, datetime) for k in histogram.keys()])


def test_get_observations(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations',
        json=load_sample_data('get_observations_node_page1.json'),
        status_code=200,
    )

    observations = get_observations(
        taxon_name='Danaus plexippus',
        created_on='2020-08-27',
        photos=True,
        geo=True,
        geoprivacy='open',
        place_id=7953,
    )
    first_result = observations['results'][0]

    assert observations['total_results'] == 2
    assert len(observations['results']) == 1
    assert first_result['taxon_geoprivacy'] == 'open'
    assert first_result['created_at'] == datetime(2020, 8, 27, 18, 0, 51, tzinfo=tzutc())
    assert first_result['observed_on'] == datetime(2020, 8, 27, 8, 57, 22, tzinfo=tzoffset('Etc/UTC', 0))
    assert first_result['taxon']['id'] == 48662
    assert len(first_result['place_ids']) == 13


@patch('pyinaturalist.pagination.sleep')
def test_get_observations__all_pages(sleep, requests_mock):
    page_1 = load_sample_data('get_observations_node_page1.json')
    page_2 = load_sample_data('get_observations_node_page2.json')

    requests_mock.get(
        f'{API_V1_BASE_URL}/observations',
        [
            {'json': page_1, 'status_code': 200},
            {'json': page_2, 'status_code': 200},
        ],
    )

    observations = get_observations(id=[57754375, 57707611], page='all')

    assert len(observations['results']) == 2


def test_get_observation_observers(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations/observers',
        json=load_sample_data('get_observation_observers_node_page1.json'),
        status_code=200,
    )

    observers = get_observation_observers(place_id=125323)
    first_result = observers['results'][0]

    assert observers['total_results'] == 4
    assert len(observers['results']) == 2
    assert first_result['user']['spam'] is False
    assert first_result['user']['suspended'] is False


def test_get_observation_identifiers(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations/identifiers',
        json=load_sample_data('get_observation_identifiers_node_page1.json'),
        status_code=200,
    )

    identifiers = get_observation_identifiers(place_id=125323, iconic_taxa='Amphibia')
    first_result = identifiers['results'][0]

    assert identifiers['total_results'] == 6
    assert len(identifiers['results']) == 3
    assert first_result['user']['spam'] is False
    assert first_result['user']['suspended'] is False


def test_get_non_existent_observation(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations',
        json=load_sample_data('get_nonexistent_observation.json'),
        status_code=200,
    )
    with pytest.raises(ObservationNotFound):
        get_observation(99999999)


def test_get_observation_species_counts(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations/species_counts',
        json=load_sample_data('get_observation_species_counts.json'),
        status_code=200,
    )
    response = get_observation_species_counts(user_login='my_username', quality_grade='research')
    first_result = response['results'][0]

    assert first_result['count'] == 31
    assert first_result['taxon']['id'] == 48484
    assert first_result['taxon']['name'] == 'Harmonia axyridis'


@patch('pyinaturalist.pagination.sleep')
def test_get_observation_species_counts__all_pages(sleep, requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations/species_counts',
        [
            {
                'json': load_sample_data('get_all_observation_species_counts_page1.json'),
                'status_code': 200,
            },
            {
                'json': load_sample_data('get_all_observation_species_counts_page2.json'),
                'status_code': 200,
            },
        ],
    )
    response = get_observation_species_counts(
        user_login='my_username', quality_grade='research', page='all'
    )
    first_result = response['results'][0]
    last_result = response['results'][-1]

    assert len(response['results']) == 22
    assert first_result['count'] == 19
    assert first_result['taxon']['id'] == 27805
    assert first_result['taxon']['name'] == 'Notophthalmus viridescens'
    assert last_result['count'] == 1
    assert last_result['taxon']['id'] == 39556
    assert last_result['taxon']['name'] == 'Apalone spinifera'


def test_get_observation_species_counts__invalid_multiple_choice_params():
    with pytest.raises(ValueError):
        get_observation_species_counts(quality_grade='None', iconic_taxa='slime molds')


def test_get_observation_taxonomy(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations/taxonomy',
        json=load_sample_data('get_observation_taxonomy.json'),
        status_code=200,
    )
    response = get_observation_taxonomy(user_id=12345)
    first_result = response['results'][0]

    assert response['count_without_taxon'] == 4
    assert first_result['id'] == 1
    assert first_result['name'] == 'Animalia'
    assert first_result['descendant_obs_count'] == 3023
