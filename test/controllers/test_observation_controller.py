# flake8: noqa: F405
from datetime import datetime

from dateutil.tz import tzutc

from pyinaturalist.client import iNatClient
from pyinaturalist.constants import API_V1
from pyinaturalist.models import (
    Annotation,
    ConservationStatus,
    LifeList,
    ListedTaxon,
    Observation,
    ObservationFieldValue,
    Place,
    TaxonCounts,
    TaxonSummary,
    User,
)
from test.sample_data import *


def test_from_id(requests_mock):
    observation_id = 16227955
    requests_mock.get(
        f'{API_V1}/observations/16227955',
        json=SAMPLE_DATA['get_observations_by_id'],
        status_code=200,
    )
    result = iNatClient().observations(observation_id)

    assert isinstance(result, Observation)
    assert result.id == observation_id


def test_from_id__not_found(requests_mock):
    observation_id = 16227955
    requests_mock.get(
        f'{API_V1}/observations/16227955',
        json={'results': [], 'total_results': 0},
        status_code=200,
    )
    assert iNatClient().observations(observation_id) is None


def test_from_ids(requests_mock):
    observation_id = 16227955
    obs = SAMPLE_DATA['get_observations_by_id']['results'][0]
    requests_mock.get(
        f'{API_V1}/observations/16227955',
        json={'results': [obs, obs], 'total_results': 2},
        status_code=200,
    )
    results = iNatClient().observations.from_ids(observation_id).all()

    assert len(results) == 2 and isinstance(results[0], Observation)
    assert results[0].id == observation_id


def test_from_ids__limit(requests_mock):
    observation_id = 16227955
    requests_mock.get(
        f'{API_V1}/observations/16227955',
        [
            {'json': SAMPLE_DATA['get_observations_by_id'], 'status_code': 200},
            {'json': SAMPLE_DATA['get_observations_by_id'], 'status_code': 200},
        ],
    )
    results = iNatClient().observations.from_ids(observation_id).limit(1)

    assert len(results) == 1 and isinstance(results[0], Observation)
    assert results[0].id == observation_id


def test_search(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations',
        json=SAMPLE_DATA['get_observations_node_page1'],
        status_code=200,
    )
    results = (
        iNatClient()
        .observations.search(taxon_name='Danaus plexippus', created_on='2020-08-27')
        .all()
    )

    assert isinstance(results[0], Observation)
    assert results[0].id == 57754375
    assert results[0].taxon.id == 48662
    assert results[0].created_at == datetime(2020, 8, 27, 18, 0, 51, tzinfo=tzutc())


def test_search__with_ofvs(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations',
        json=SAMPLE_DATA['get_observation_with_ofvs'],
        status_code=200,
    )
    requests_mock.get(
        f'{API_V1}/controlled_terms',
        json={'results': [], 'total_results': 0},
        status_code=200,
    )
    results = iNatClient().observations.search().all()

    ofv = results[0].ofvs[0]
    assert isinstance(ofv, ObservationFieldValue)
    assert ofv.datatype == 'taxon'
    assert ofv.value == 119900


def test_search__with_annotations(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations',
        json=SAMPLE_DATA['get_observation_with_ofvs'],
        status_code=200,
    )
    requests_mock.get(
        f'{API_V1}/controlled_terms',
        json=SAMPLE_DATA['get_controlled_terms'],
        status_code=200,
    )
    results = iNatClient().observations.search().all()
    annotation = results[0].annotations[0]

    assert isinstance(annotation, Annotation)
    assert annotation.controlled_attribute.label == 'Life Stage'
    assert annotation.controlled_value.label == 'Adult'


def test_histogram(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations/histogram',
        json=SAMPLE_DATA['get_observation_histogram_day'],
        status_code=200,
    )
    results = iNatClient().observations.histogram(user_id='username')

    assert len(results) == 31
    assert results[datetime(2020, 1, 1, 0, 0)] == 11


def test_identifiers(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations/identifiers',
        json=j_observation_identifiers,
        status_code=200,
    )
    results = iNatClient().observations.identifiers(place_id=125323, iconic_taxa='Amphibia')

    assert len(results) == 3 and isinstance(results[0], User)
    assert results[0].id == 112514
    assert results[0].login == 'earthstephen'
    assert results[0].count == 1


def test_observers(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations/observers',
        json=j_observation_observers,
        status_code=200,
    )
    results = iNatClient().observations.observers(place_id=125323, iconic_taxa='Amphibia')

    assert len(results) == 2 and isinstance(results[0], User)
    assert results[0].id == 53153
    assert results[0].login == 'willkuhn'
    assert results[0].count == results[0].observation_count == 750
    assert results[0].species_count == 1230


def test_life_list(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations/taxonomy',
        json=j_life_list,
        status_code=200,
    )
    client = iNatClient()
    results = client.observations.life_list('username')

    assert isinstance(results, LifeList)
    assert results[0].id == 1
    assert results[0].name == 'Animalia'
    assert results[0].direct_obs_count == 1
    assert results[0].descendant_obs_count == results.get_count(1) == 3023


def test_popular_fields(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations/popular_field_values',
        json=SAMPLE_DATA['get_observation_popular_field_values'],
        status_code=200,
    )
    client = iNatClient()
    results = client.observations.popular_fields(species_name='Danaus plexippus', place_id=24)
    assert results[0].count == 231
    assert results[0].histogram[10] == 29
    assert results[0].controlled_attribute.id == 1
    assert results[0].controlled_value.id == 2
    assert results[0].controlled_attribute.label == results[0].term == 'Life Stage'
    assert results[0].controlled_value.label == results[0].value == 'Adult'


def test_species_counts(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations/species_counts',
        json=SAMPLE_DATA['get_observation_species_counts'],
        status_code=200,
    )
    client = iNatClient()
    results = client.observations.species_counts(user_id='username')

    assert isinstance(results, TaxonCounts)
    assert results[0].rank == 'species'
    assert results[0].name == 'Harmonia axyridis'
    assert results[0].id == 48484
    assert results[0].count == results.get_count(48484) == 31


def test_taxon_summary__with_conservation_status(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations/89238647/taxon_summary',
        json=j_taxon_summary_1_conserved,
        status_code=200,
    )
    client = iNatClient()
    results = client.observations.taxon_summary(89238647)

    assert isinstance(results, TaxonSummary)
    assert isinstance(results.conservation_status, ConservationStatus)
    assert results.conservation_status.taxon_id == 4747
    assert results.conservation_status.status == 'NT'


def test_taxon_summary__with_listed_taxon(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations/7849808/taxon_summary',
        json=j_taxon_summary_2_listed,
        status_code=200,
    )
    client = iNatClient()
    results = client.observations.taxon_summary(7849808)
    lt = results.listed_taxon

    assert isinstance(results, TaxonSummary)
    assert isinstance(lt, ListedTaxon)
    assert isinstance(lt.place, Place)
    assert lt.list.id == 2684267
    assert lt.taxon_id == 47219
    assert lt.place.id == 144952
    assert lt.establishment_means == lt.establishment_means_label == 'introduced'
    assert 'western honey bee' in results.wikipedia_summary


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
