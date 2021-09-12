# flake8: noqa: F405
import re

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
    [j_listed_taxon_1, j_listed_taxon_2_partial],
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
        return str(
            value.get('id') or value.get('record', {}).get('id') or value.get('taxon', {}).get('id')
        )

    # Just make sure at least object IDs show up in the table
    console = Console()
    rendered = '\n'.join([str(line) for line in console.render_lines(table)])

    if isinstance(response, list):
        assert all([_get_id(value) in rendered for value in response])

    # for obj in response:
    #     assert all([value in rendered_table for value in obj.row.values()])


# TODO: Test content written to stdout. For now, just make sure it doesn't explode.
@pytest.mark.parametrize('response', TABULAR_RESPONSES)
def test_pprint(response):
    console = Console(force_terminal=False, width=120)
    with console.capture() as output:
        pprint(response)
    rendered = output.get()


@pytest.mark.parametrize('input', get_variations(j_controlled_term_1))
def test_format_controlled_terms(input):
    assert (
        format_controlled_terms(input)
        == '[12] Plant Phenology: No Evidence of Flowering, Flowering, Fruiting, Flower Budding'
    )


@pytest.mark.parametrize('input', get_variations(j_identification_1))
def test_format_identifications(input):
    expected_str = '[155554373] Species: 60132 (supporting) added on Feb 18, 2021 by jkcook'
    assert format_identifications(input) == expected_str


@pytest.mark.parametrize('input', get_variations(j_observation_1))
def test_format_observation(input):
    expected_str = (
        '[16227955] 🪲 Species: Lixus bardanae observed on Sep 05, 2018 '
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


PRINTED_OBSERVATION = """
Observation(
    id=16227955,
    created_at=datetime.datetime(2018, 9, 5, 0, 0, tzinfo=tzoffset('Europe/Paris', 3600)),
    captive=False,
    community_taxon_id=493595,
    description='',
    faves=[],
    geoprivacy=None,
    identifications_count=2,
    identifications_most_agree=True,
    identifications_most_disagree=False,
    identifications_some_agree=True,
    license_code='CC0',
    location=(50.646894, 4.360086),
    mappable=True,
    num_identification_agreements=2,
    num_identification_disagreements=0,
    oauth_application_id=None,
    obscured=False,
    observed_on=datetime.datetime(2018, 9, 5, 14, 6, tzinfo=tzoffset('Europe/Paris', 3600)),
    outlinks=[{'source': 'GBIF', 'url': 'http://www.gbif.org/occurrence/1914197587'}],
    out_of_range=None,
    owners_identification_from_vision=True,
    place_guess='54 rue des Badauds',
    place_ids=[7008, 8657, 14999, 59614, 67952, 80627, 81490, 96372, 96794, 97391, 97582, 108692],
    positional_accuracy=23,
    preferences={'prefers_community_taxon': None},
    project_ids=[],
    project_ids_with_curator_id=[],
    project_ids_without_curator_id=[],
    public_positional_accuracy=23,
    quality_grade='research',
    quality_metrics=[],
    reviewed_by=[180811, 886482, 1226913],
    site_id=1,
    sounds=[],
    species_guess='Lixus bardanae',
    tags=[],
    updated_at=datetime.datetime(2018, 9, 22, 19, 19, 27, tzinfo=tzoffset(None, 7200)),
    uri='https://www.inaturalist.org/observations/16227955',
    uuid='6448d03a-7f9a-4099-86aa-ca09a7740b00',
    votes=[],
    annotations=[],
    comments=[
        borisb on Sep 05, 2018: I now see: Bonus species on observation! You ma...,
        borisb on Sep 05, 2018: suspect L. bardanae - but sits on Solanum (non-...
    ],
    identifications=[
        [34896306] 🪲 Genus: Lixus (improving) added on Sep 05, 2018 by niconoe,
        [34926789] 🪲 Species: Lixus bardanae (improving) added on Sep 05, 2018 by borisb,
        [36039221] 🪲 Species: Lixus bardanae (supporting) added on Sep 22, 2018 by jpreudhomme
    ],
    ofvs=[],
    photos=[
        [24355315] https://static.inaturalist.org/photos/24355315/original.jpeg?1536150664 (CC-BY, 1445x1057),
        [24355313] https://static.inaturalist.org/photos/24355313/original.jpeg?1536150659 (CC-BY, 2048x1364)
    ],
    project_observations=[],
    taxon=[493595] 🪲 Species: Lixus bardanae,
    user=[886482] niconoe (Nicolas Noé)
)
"""


def test_get_model_fields():
    """Ensure that nested model objects are included in get_model_fields() output"""
    observation = Observation.from_json(j_observation_1)
    model_fields = get_model_fields(observation)

    n_nested_model_objects = 8
    n_regular_attrs = len(Observation.__attrs_attrs__)
    assert len(model_fields) == n_regular_attrs + n_nested_model_objects


def test_pretty_print():
    """Test rich.pretty with modifications, via get_model_fields()"""
    console = Console(force_terminal=False, width=120)
    observation = Observation.from_json(j_observation_1)

    with console.capture() as output:
        console.print(observation)
    rendered = output.get()

    # Don't check for differences in indendtation
    rendered = re.sub(' +', ' ', rendered.strip())
    expected = re.sub(' +', ' ', PRINTED_OBSERVATION.strip())
    assert rendered == expected
