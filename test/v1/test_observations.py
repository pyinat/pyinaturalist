# flake8: noqa: F405
from datetime import datetime
from io import BytesIO
from unittest.mock import patch

import pytest
from dateutil.tz import tzoffset, tzutc

from pyinaturalist.constants import API_V1
from pyinaturalist.exceptions import ObservationNotFound
from pyinaturalist.v1 import (
    create_observation,
    delete_observation,
    get_observation,
    get_observation_histogram,
    get_observation_identifiers,
    get_observation_observers,
    get_observation_popular_field_values,
    get_observation_species_counts,
    get_observation_taxon_summary,
    get_observation_taxonomy,
    get_observations,
    get_observations_by_id,
    update_observation,
    upload,
)
from test.sample_data import SAMPLE_DATA, j_taxon_summary_1_conserved, j_taxon_summary_2_listed


def test_get_observation(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations',
        json=SAMPLE_DATA['get_observation'],
        status_code=200,
    )

    observation = get_observation(16227955)
    assert observation['quality_grade'] == 'research'
    assert observation['id'] == 16227955
    assert observation['user']['login'] == 'niconoe'
    assert len(observation['photos']) == 2


def test_get_observation_histogram(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations/histogram',
        json=SAMPLE_DATA['get_observation_histogram_month'],
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
        f'{API_V1}/observations',
        json=SAMPLE_DATA['get_observations_node_page1'],
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
    assert first_result['observed_on'] == datetime(
        2020, 8, 27, 8, 57, 22, tzinfo=tzoffset('Etc/UTC', 0)
    )
    assert first_result['taxon']['id'] == 48662
    assert len(first_result['place_ids']) == 13


def test_get_observations__all_pages(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations',
        [
            {'json': SAMPLE_DATA['get_observations_node_page1'], 'status_code': 200},
            {'json': SAMPLE_DATA['get_observations_node_page2'], 'status_code': 200},
        ],
    )

    observations = get_observations(id=[57754375, 57707611], per_page=1, page='all')
    assert len(observations['results']) == 2


def test_get_observations_by_id(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations/493595',
        json=SAMPLE_DATA['get_observations_by_id'],
        status_code=200,
    )

    observations = get_observations_by_id(493595)
    first_result = observations['results'][0]

    assert observations['total_results'] == len(observations['results']) == 1
    assert first_result['created_at'] == datetime(
        2018, 9, 5, 14, 31, 8, tzinfo=tzoffset(None, 7200)
    )
    assert first_result['observed_on'] == datetime(2018, 9, 5, 14, 6, tzinfo=tzoffset(None, 7200))
    assert first_result['taxon']['id'] == 493595
    assert first_result['annotations'][0]['controlled_attribute']['id'] == 1


def test_get_observations_by_id__multiple(requests_mock):
    obs = SAMPLE_DATA['get_observations_by_id']['results'][0]
    requests_mock.get(
        f'{API_V1}/observations/493595,12345',
        json={'results': [obs, obs], 'total_results': 2},
        status_code=200,
    )

    observations = get_observations_by_id([493595, 12345])
    assert observations['total_results'] == len(observations['results']) == 2


def test_get_observation__non_existent(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations',
        json=SAMPLE_DATA['get_nonexistent_observation'],
        status_code=200,
    )
    with pytest.raises(ObservationNotFound):
        get_observation(99999999)


def test_get_observation_identifiers(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations/identifiers',
        json=SAMPLE_DATA['get_observation_identifiers_node_page1'],
        status_code=200,
    )

    identifiers = get_observation_identifiers(place_id=125323, iconic_taxa='Amphibia')
    first_result = identifiers['results'][0]

    assert identifiers['total_results'] == 6
    assert len(identifiers['results']) == 3
    assert first_result['user']['spam'] is False
    assert first_result['user']['suspended'] is False


def test_get_observation_observers(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations/observers',
        json=SAMPLE_DATA['get_observation_observers_node_page1'],
        status_code=200,
    )

    observers = get_observation_observers(place_id=125323)
    first_result = observers['results'][0]

    assert observers['total_results'] == 4
    assert len(observers['results']) == 2
    assert first_result['user']['spam'] is False
    assert first_result['user']['suspended'] is False


def test_get_observation_popular_field_values(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations/popular_field_values',
        json=SAMPLE_DATA['get_observation_popular_field_values'],
        status_code=200,
    )

    response = get_observation_popular_field_values(species_name='Danaus plexippus', place_id=24)
    first_result = response['results'][0]
    assert first_result['count'] == 231
    assert first_result['month_of_year'][10] == 29
    assert first_result['controlled_attribute']['id'] == 1
    assert first_result['controlled_value']['label'] == 'Adult'


def test_get_observation_species_counts(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations/species_counts',
        json=SAMPLE_DATA['get_observation_species_counts'],
        status_code=200,
    )
    response = get_observation_species_counts(user_login='my_username', quality_grade='research')
    first_result = response['results'][0]

    assert first_result['count'] == 31
    assert first_result['taxon']['id'] == 48484
    assert first_result['taxon']['name'] == 'Harmonia axyridis'


def test_get_observation_species_counts__all_pages(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations/species_counts',
        [
            {
                'json': SAMPLE_DATA['get_all_observation_species_counts_page1'],
                'status_code': 200,
            },
            {
                'json': SAMPLE_DATA['get_all_observation_species_counts_page2'],
                'status_code': 200,
            },
        ],
    )
    response = get_observation_species_counts(
        user_login='my_username', quality_grade='research', per_page=1, page='all'
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
        f'{API_V1}/observations/taxonomy',
        json=SAMPLE_DATA['get_observation_taxonomy'],
        status_code=200,
    )
    response = get_observation_taxonomy(user_id=12345)
    first_result = response['results'][0]

    assert response['count_without_taxon'] == 4
    assert first_result['id'] == 1
    assert first_result['name'] == 'Animalia'
    assert first_result['descendant_obs_count'] == 3023


def test_get_observation_taxon_summary__with_conservation_status(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations/89238647/taxon_summary',
        json=j_taxon_summary_1_conserved,
        status_code=200,
    )
    response = get_observation_taxon_summary(89238647)
    assert response['conservation_status']['taxon_id'] == 4747
    assert response['conservation_status']['status'] == 'NT'
    assert response['conservation_status']['created_at'] == datetime(
        2013, 2, 16, 0, 50, 56, 264000, tzinfo=tzutc()
    )


def test_get_observation_taxon_summary__with_listed_taxon(requests_mock):
    requests_mock.get(
        f'{API_V1}/observations/7849808/taxon_summary',
        json=j_taxon_summary_2_listed,
        status_code=200,
    )
    response = get_observation_taxon_summary(7849808)
    assert response['listed_taxon']['taxon_id'] == 47219
    assert response['listed_taxon']['place']['id'] == 144952
    assert response['listed_taxon']['created_at'] == datetime(
        2019, 11, 20, 16, 26, 47, 604000, tzinfo=tzutc()
    )
    assert 'western honey bee' in response['wikipedia_summary']


def test_create_observation(requests_mock):
    requests_mock.post(
        f'{API_V1}/observations',
        json=SAMPLE_DATA['create_observation_v1'],
        status_code=200,
    )

    response = create_observation(
        species_guess='Pieris rapae', observed_on='2021-09-09', access_token='token'
    )
    assert response['id'] == 54986584
    assert response['uuid'] == '3595235e-96b1-450f-92ec-49162721cc6f'


@patch('pyinaturalist.v1.observations.upload')
@patch('pyinaturalist.v1.observations.post')
def test_create_observation__with_files(mock_post, mock_upload):
    create_observation(
        access_token='token',
        photos=['photo_1.jpg', 'photo_2.jpg'],
        sounds=['sound_1.mp3', 'sound_2.wav'],
        photo_ids=[12345],
    )

    request_params = mock_post.call_args[1]['json']['observation']
    assert 'local_photos' not in request_params
    assert 'sounds' not in request_params
    assert 'photo_ids' not in request_params
    mock_upload.assert_called_once()


def test_update_observation(requests_mock):
    requests_mock.put(
        f'{API_V1}/observations/17932425',
        json=SAMPLE_DATA['update_observation_result'],
        status_code=200,
    )
    response = update_observation(
        17932425, access_token='valid token', description='updated description v2 !'
    )

    # If all goes well we got a single element representing the updated observation, enclosed in a list.
    assert len(response) == 1
    assert response[0]['id'] == 17932425
    assert response[0]['description'] == 'updated description v2 !'


@patch('pyinaturalist.v1.observations.upload')
@patch('pyinaturalist.v1.observations.put')
def test_update_observation__with_photos(mock_put, mock_upload):
    update_observation(1234, access_token='token', photos='photo.jpg')

    request_args = mock_put.call_args[1]
    obs_params = request_args['json']['observation']
    assert request_args['ignore_photos'] == 1
    assert 'local_photos' not in obs_params
    assert 'sounds' not in obs_params
    mock_upload.assert_called_once()


@patch('pyinaturalist.v1.observations.get_observation')
@patch('pyinaturalist.v1.observations.put')
def test_update_observation__with_photo_ids(mock_put, mock_get_observation):
    mock_get_observation.return_value = {'photos': [{'id': 1234}]}
    update_observation(1234, access_token='token', photo_ids=5678)

    payload = mock_put.call_args[1]['json']
    assert 'photo_ids' not in payload
    assert payload['local_photos'] == {'1234': [1234, 5678]}


@patch('pyinaturalist.v1.observations.put')
def test_update_observation__remove_existing_photos(mock_put):
    update_observation(1234, access_token='token', ignore_photos=False)

    request_args = mock_put.call_args[1]
    assert 'ignore_photos' not in request_args


def test_upload(requests_mock):
    requests_mock.post(
        f'{API_V1}/observation_photos',
        json=SAMPLE_DATA['post_observation_photos'],
        status_code=200,
    )
    requests_mock.post(
        f'{API_V1}/observation_sounds',
        json=SAMPLE_DATA['post_observation_sounds'],
        status_code=200,
    )

    response = upload(1234, BytesIO(), BytesIO(), access_token='token')
    assert response[0]['id'] == 1234
    assert response[0]['created_at'] == '2020-09-24T21:06:16.964-05:00'
    assert response[0]['photo']['native_username'] == 'username'

    assert response[1]['id'] == 233946
    assert response[1]['created_at'] == '2021-05-30T17:36:40.286-05:00'
    assert response[1]['sound']['file_content_type'] == 'audio/mpeg'


@patch('pyinaturalist.v1.observations.update_observation')
def test_upload__with_photo_ids(mock_update_observation):
    upload(1234, access_token='token', photo_ids=[5678])
    mock_update_observation.assert_called_with(1234, access_token='token', photo_ids=[5678])


def test_delete_observation(requests_mock):
    requests_mock.delete(f'{API_V1}/observations/24774619', status_code=200)
    response = delete_observation(observation_id=24774619, access_token='valid token')
    assert response is None
