# flake8: noqa: F405
import pytest
from rich.console import Console
from rich.table import Table

from pyinaturalist.formatters import *
from test.sample_data import *

# Lists of JSON records that can be formatted into tables
TABULAR_RESPONSES = [
    j_comments,
    [j_controlled_term_1, j_controlled_term_2],
    [j_identification_1, j_identification_2],
    [j_observation_1, j_observation_2],
    j_obs_species_counts,
    j_life_list,
    [j_photo_1, j_photo_2_partial],
    [j_place_1, j_place_2],
    j_places_nearby,
    [j_project_1, j_project_2],
    j_search_results,
    [j_taxon_1, j_taxon_2_partial],
    [j_user_1, j_user_2_partial],
]


def get_variations(response_object):
    """Formatting functions should accept any of these variations"""
    return [{'results': [response_object]}, [response_object], response_object]


# TODO: More thorough tests for table content
@pytest.mark.parametrize('response', TABULAR_RESPONSES)
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
@pytest.mark.parametrize('response', TABULAR_RESPONSES)
def test_pprint(response):
    pprint(response)


@pytest.mark.parametrize('input', get_variations(j_controlled_term_1))
def test_format_controlled_terms(input):
    assert (
        format_controlled_terms(input)
        == '[12] Plant Phenology: No Evidence of Flowering, Flowering, Fruiting, Flower Budding'
    )


@pytest.mark.parametrize('input', get_variations(j_identification_1))
def test_format_identifications(input):
    expected_str = '[155554373] Species: 60132 (supporting) added on 2021-02-18 20:31:32-06:00 by jkcook'
    assert format_identifications(input) == expected_str


@pytest.mark.parametrize('input', get_variations(j_observation_1))
def test_format_observation(input):
    expected_str = (
        '[16227955] 🪲 Species: Lixus bardanae observed on 2018-09-05 14:06:00+01:00 '
        'by niconoe at 54 rue des Badauds'
    )
    assert format_observations(input) == expected_str


@pytest.mark.parametrize('input', get_variations(j_project_1))
def test_format_projects(input):
    expected_str = '[8291] PNW Invasive Plant EDDR'
    assert format_projects(input) == expected_str


@pytest.mark.parametrize('input', get_variations(j_place_1))
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
    assert format_places(j_places_nearby) == places_str


def test_format_search_results():
    expected_str = (
        '[Taxon] [47792] 🐛 Order: Odonata (Dragonflies and Damselflies)\n'
        '[Place] [113562] Odonates of Peninsular India and Sri Lanka\n'
        '[Project] [9978] Ohio Dragonfly Survey  (Ohio Odonata Survey)\n'
        '[User] [113886] odonatanb (Gilles Belliveau)'
    )
    assert format_search_results(j_search_results) == expected_str


@pytest.mark.parametrize('input', get_variations(j_species_count_1))
def test_format_species_counts(input):
    expected_str = '[48484] 🐞 Species: Harmonia axyridis (Asian Lady Beetle): 31'
    assert format_species_counts(input) == expected_str


@pytest.mark.parametrize('input', get_variations(j_taxon_1))
def test_format_taxa__with_common_name(input):
    expected_str = '[70118] 🪲 Species: Nicrophorus vespilloides (Lesser Vespillo Burying Beetle)'
    assert format_taxa(input) == expected_str


@pytest.mark.parametrize('input', get_variations(j_taxon_3_no_common_name))
def test_format_taxon__without_common_name(input):
    assert format_taxa(input) == '[124162] 🪰 Species: Temnostoma vespiforme'


@pytest.mark.parametrize('input', get_variations(j_user_2_partial))
def test_format_users(input):
    expected_str = '[886482] niconoe (Nicolas Noé)'
    assert format_users(input) == expected_str


def test_simplify_observation():
    simplified_obs = simplify_observations(j_observation_1)
    # Not much worth testing here, just make sure it returns something that can be formatted
    assert format_observations(simplified_obs)
