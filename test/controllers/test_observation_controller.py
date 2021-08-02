from datetime import datetime

from dateutil.tz import tzutc

from pyinaturalist.client import iNatClient
from pyinaturalist.constants import API_V1_BASE_URL
from pyinaturalist.models import LifeList, Observation, TaxonCounts, User
from test.conftest import load_sample_data


def test_from_id(requests_mock):
    observation_id = 57754375
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations',
        json=load_sample_data('get_observations_node_page1.json'),
        status_code=200,
    )

    client = iNatClient()
    results = client.observations.from_id(observation_id)
    assert len(results) == 1 and isinstance(results[0], Observation)
    assert results[0].id == observation_id


def test_search(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations',
        json=load_sample_data('get_observations_node_page1.json'),
        status_code=200,
    )

    client = iNatClient()
    results = client.observations.search(taxon_name='Danaus plexippus', created_on='2020-08-27')
    assert isinstance(results[0], Observation)
    assert results[0].id == 57754375
    assert results[0].taxon.id == 48662
    assert results[0].created_at == datetime(2020, 8, 27, 18, 0, 51, tzinfo=tzutc())


def test_histogram(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations/histogram',
        json=load_sample_data('get_observation_histogram_day.json'),
        status_code=200,
    )

    client = iNatClient()
    results = client.observations.histogram(user_id='username')
    assert len(results) == 31
    assert results[datetime(2020, 1, 1, 0, 0)] == 11


def test_identifiers(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations/identifiers',
        json=load_sample_data('get_observation_identifiers_node_page1.json'),
        status_code=200,
    )

    client = iNatClient()
    results = client.observations.identifiers(place_id=125323, iconic_taxa='Amphibia')
    assert len(results) == 3 and isinstance(results[0], User)

    assert results[0].id == 112514
    assert results[0].login == 'earthstephen'
    assert results[0].count == 1


def test_observers(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations/observers',
        json=load_sample_data('get_observation_observers_node_page1.json'),
        status_code=200,
    )

    client = iNatClient()
    results = client.observations.observers(place_id=125323, iconic_taxa='Amphibia')
    assert len(results) == 2 and isinstance(results[0], User)

    assert results[0].id == 53153
    assert results[0].login == 'willkuhn'
    assert results[0].count == results[0].observation_count == 750
    assert results[0].species_count == 1230


def test_life_list(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations/taxonomy',
        json=load_sample_data('get_observation_taxonomy.json'),
        status_code=200,
    )

    client = iNatClient()
    results = client.observations.life_list('username')
    assert isinstance(results, LifeList)
    assert results[0].id == 1
    assert results[0].name == 'Animalia'
    assert results[0].direct_obs_count == 1
    assert results[0].descendant_obs_count == results.get_count(1) == 3023


def test_species_counts(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations/species_counts',
        json=load_sample_data('get_observation_species_counts.json'),
        status_code=200,
    )
    client = iNatClient()
    results = client.observations.species_counts(user_id='username')
    assert isinstance(results, TaxonCounts)
    assert results[0].rank == 'species'
    assert results[0].name == 'Harmonia axyridis'
    assert results[0].id == 48484
    assert results[0].count == results.get_count(48484) == 31


# TODO:
# def test_create():
#     client = iNatClient()
#     results = client.observations.create()


# def test_delete():
#     client = iNatClient()
#     results = client.observations.delete()


# def test_upload():
#     client = iNatClient()
#     results = client.observations.upload()
