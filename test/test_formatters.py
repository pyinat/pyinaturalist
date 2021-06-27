import pytest

from rich.console import Console
from rich.table import Table

from pyinaturalist.formatters import (
    format_controlled_terms,
    format_identifications,
    format_observations,
    format_places,
    format_projects,
    format_search_results,
    format_species_counts,
    format_table,
    format_taxa,
    format_users,
    pprint,
    simplify_observations,
)
from pyinaturalist.models import LifeList
from test.conftest import load_sample_data

controlled_term_1 = load_sample_data('get_controlled_terms.json')['results'][0]
controlled_term_2 = load_sample_data('get_controlled_terms.json')['results'][1]
identification_1 = load_sample_data('get_identifications.json')['results'][0]
identification_2 = load_sample_data('get_identifications.json')['results'][1]
observation_1 = load_sample_data('get_observation.json')['results'][0]
observation_2 = load_sample_data('get_observations_node_page1.json')['results'][0]
obs_taxonomy_json = load_sample_data('get_observation_taxonomy.json')
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

comments = observation_2['comments']
life_list = LifeList.from_json(obs_taxonomy_json)
photo = taxon_1['default_photo']

RESPONSES = [
    comments,
    [controlled_term_1, controlled_term_2],
    [identification_1, identification_2],
    [observation_1, observation_2],
    [photo, photo],
    [place_1, place_2],
    places_nearby,
    [project_1, project_2],
    search_results,
    [taxon_1, taxon_2],
    [user_1, user_2],
    life_list,
]


def get_variations(response_object):
    """Formatting functions should accept any of these variations"""
    return [{'results': [response_object]}, [response_object], response_object]


# TODO: More thorough tests for table content
@pytest.mark.parametrize('response', RESPONSES)
def test_format_table(response):
    table = format_table(response)
    assert isinstance(table, Table)

    def _get_id(value):
        return str(value.get('id') or value.get('record', {}).get('id'))

    # Just make sure at least object IDs show up in the table
    console = Console()
    rendered_table = '\n'.join([str(line) for line in console.render_lines(table)])
    if isinstance(response, list):
        assert all([_get_id(value) in rendered_table for value in response])

    # for obj in response:
    #     assert all([value in rendered_table for value in obj.row.values()])


# TODO: Test content written to stdout. For now, just make sure it doesn't explode.
@pytest.mark.parametrize('response', RESPONSES)
def test_pprint(response):
    pprint(response)


@pytest.mark.parametrize('input', get_variations(controlled_term_1))
def test_format_controlled_terms(input):
    assert (
        format_controlled_terms(input)
        == '[12] Plant Phenology: No Evidence of Flowering, Flowering, Fruiting, Flower Budding'
    )


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
[97394] North America
[97395] Asia
[97393] Oceania
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
