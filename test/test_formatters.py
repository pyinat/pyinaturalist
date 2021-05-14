import pytest

from pyinaturalist.formatters import (
    format_observations,
    format_species_counts,
    format_taxa,
    simplify_observations,
)
from test.conftest import load_sample_data

observation_1 = load_sample_data('get_observation.json')['results'][0]
observation_2 = load_sample_data('get_observations_node_page1.json')['results'][0]
species_count_1 = load_sample_data('get_observation_species_counts.json')['results'][0]
species_count_2 = load_sample_data('get_observation_species_counts.json')['results'][1]
taxon_1 = load_sample_data('get_taxa.json')['results'][0]
taxon_2 = load_sample_data('get_taxa.json')['results'][2]


def get_variations(response_object):
    """Formatting functions should accept any of these variations"""
    return [{'results': [response_object]}, [response_object], response_object]


@pytest.mark.parametrize('input', get_variations(observation_1))
def test_format_observation(input):
    assert format_observations(input) == (
        '[16227955] [493595] Species: Lixus bardanae '
        'observed by niconoe on 2018-09-05 at 54 rue des Badauds'
    )


def test_format_observation__align():
    expected_str = (
        '[16227955] [  493595]      Species                                          Lixus bardanae\n'
        '    observed by niconoe on 2018-09-05 at 54 rue des Badauds\n'
        '[57754375] [   48662]      Species                              Danaus plexippus (Monarch)\n'
        '    observed by samroom on 2020-08-27 at Railway Ave, Wilcox, SK, CA'
    )
    assert format_observations([observation_1, observation_2], align=True) == expected_str


@pytest.mark.parametrize('input', get_variations(species_count_1))
def test_format_species_counts(input):
    expected_str = '[48484] Species: Harmonia axyridis (Asian Lady Beetle): 31'
    assert format_species_counts(input) == expected_str


def test_format_species_counts__align():
    expected_str = (
        '[   48484]      Species                   Harmonia axyridis (Asian Lady Beetle): 31\n'
        '[   51702]      Species   Coccinella septempunctata (Seven-spotted Lady Beetle): 19'
    )
    assert format_species_counts([species_count_1, species_count_2], align=True) == expected_str


@pytest.mark.parametrize('input', get_variations(taxon_1))
def test_format_taxa__with_common_name(input):
    expected_str = '[70118] Species: Nicrophorus vespilloides (Lesser Vespillo Burying Beetle)'
    assert format_taxa(input) == expected_str


@pytest.mark.parametrize('input', get_variations(taxon_2))
def test_format_taxon__without_common_name(input):
    assert format_taxa(input) == '[124162] Species: Temnostoma vespiforme'


def test_format_taxa__align():
    expected_str = (
        '[   70118]      Species Nicrophorus vespilloides (Lesser Vespillo Burying Beetle)\n'
        '[  124162]      Species                                   Temnostoma vespiforme'
    )
    x = format_taxa([taxon_1, taxon_2], align=True)
    print(x)
    assert format_taxa([taxon_1, taxon_2], align=True) == expected_str


def test_format_taxon__invalid():
    assert format_taxa(None) == 'unknown taxon'


def test_simplify_observation():
    simplified_obs = simplify_observations(observation_1)
    # Not much worth testing here, just make sure it returns something that can be formatted
    assert format_observations(simplified_obs)
