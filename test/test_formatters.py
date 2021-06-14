import pytest

from pyinaturalist.formatters import (
    format_controlled_terms,
    format_identifications,
    format_observations,
    format_places,
    format_projects,
    format_search_results,
    format_species_counts,
    format_taxa,
    format_users,
    simplify_observations,
)
from test.conftest import load_sample_data

controlled_term_1 = load_sample_data('get_controlled_terms.json')['results'][0]
controlled_term_2 = load_sample_data('get_controlled_terms.json')['results'][1]
identification_1 = load_sample_data('get_identifications.json')['results'][0]
identification_2 = load_sample_data('get_identifications.json')['results'][1]
observation_1 = load_sample_data('get_observation.json')['results'][0]
observation_2 = load_sample_data('get_observations_node_page1.json')['results'][0]
place_1 = load_sample_data('get_places_by_id.json')['results'][1]
place_2 = load_sample_data('get_places_autocomplete.json')['results'][0]
places_nearby = load_sample_data('get_places_nearby.json')['results']
places_nearby['standard'] = places_nearby['standard'][:3]
places_nearby['community'] = places_nearby['community'][:3]
project_1 = load_sample_data('get_projects.json')['results'][0]
project_2 = load_sample_data('get_projects.json')['results'][1]
search_results = load_sample_data('get_search.json')['results']
species_count_1 = load_sample_data('get_observation_species_counts.json')['results'][0]
species_count_2 = load_sample_data('get_observation_species_counts.json')['results'][1]
taxon_1 = load_sample_data('get_taxa.json')['results'][0]
taxon_2 = load_sample_data('get_taxa.json')['results'][2]
user_1 = load_sample_data('get_user_by_id.json')['results'][0]
user_2 = load_sample_data('get_users_autocomplete.json')['results'][0]


def get_variations(response_object):
    """Formatting functions should accept any of these variations"""
    return [{'results': [response_object]}, [response_object], response_object]


controlled_term_str_1 = """
12: Plant Phenology
    21: No Evidence of Flowering
    13: Flowering
    14: Fruiting
    15: Flower Budding
""".strip()
controlled_term_str_2 = """
9: Sex
    10: Female
    11: Male
    20: Cannot Be Determined
""".strip()


@pytest.mark.parametrize('input', get_variations(controlled_term_1))
def test_format_controlled_terms(input):
    assert format_controlled_terms(input) == controlled_term_str_1


@pytest.mark.parametrize('input', get_variations(identification_1))
def test_format_identifications(input):
    expected_str = '[155554373] Species: 60132 (supporting) added on 2021-02-18 20:31:32-06:00 by jkcook'
    assert format_identifications(input) == expected_str


@pytest.mark.parametrize('input', get_variations(observation_1))
def test_format_observation(input):
    expected_str = (
        '[16227955] Species: Lixus bardanae observed on 2018-09-05 14:06:00+01:00 '
        'by niconoe at 54 rue des Badauds'
    )
    assert format_observations(input) == expected_str


@pytest.mark.parametrize('input', get_variations(project_1))
def test_format_projects(input):
    expected_str = '[8291] PNW Invasive Plant EDDR'
    assert format_projects(input) == expected_str


@pytest.mark.parametrize('input', get_variations(place_1))
def test_format_places(input):
    expected_str = '[89191] Conservation Area Riversdale'
    assert format_places(input) == expected_str


def test_format_places__nearby():
    places_str = """
Standard:
[97394] North America
[97395] Asia
[97393] Oceania

Community:
[11770] Mehedinti
[119755] Mahurangi College
[150981] Ceap Breatainn
""".strip()
    assert format_places(places_nearby) == places_str


def test_format_search_results():
    expected_str = (
        '[Taxon] [47792] Order: Odonata (Dragonflies and Damselflies)\n'
        '[Place] [113562] Odonates of Peninsular India and Sri Lanka\n'
        '[Project] [9978] Ohio Dragonfly Survey  (Ohio Odonata Survey)\n'
        '[User] [113886] odonatanb (Gilles Belliveau)'
    )
    assert format_search_results(search_results) == expected_str


@pytest.mark.parametrize('input', get_variations(species_count_1))
def test_format_species_counts(input):
    expected_str = '[48484] Species: Harmonia axyridis (Asian Lady Beetle): 31'
    assert format_species_counts(input) == expected_str


@pytest.mark.parametrize('input', get_variations(taxon_1))
def test_format_taxa__with_common_name(input):
    expected_str = '[70118] Species: Nicrophorus vespilloides (Lesser Vespillo Burying Beetle)'
    assert format_taxa(input) == expected_str


@pytest.mark.parametrize('input', get_variations(taxon_2))
def test_format_taxon__without_common_name(input):
    assert format_taxa(input) == '[124162] Species: Temnostoma vespiforme'


@pytest.mark.parametrize('input', get_variations(user_2))
def test_format_users(input):
    expected_str = '[886482] niconoe (Nicolas Noé)'
    assert format_users(input) == expected_str


def test_simplify_observation():
    simplified_obs = simplify_observations(observation_1)
    # Not much worth testing here, just make sure it returns something that can be formatted
    assert format_observations(simplified_obs)
