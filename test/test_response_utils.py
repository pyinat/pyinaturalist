from pyinaturalist.response_utils import (
    format_observation_str,
    format_taxon_str,
    simplify_observation,
)
from test.conftest import load_sample_data


def test_format_observation():
    observation = load_sample_data('get_observation.json')['results'][0]
    assert format_observation_str(observation) == (
        '[16227955] Species: Lixus bardanae '
        'observed by niconoe on 2018-09-05 at 54 rue des Badauds'
    )


def test_format_taxon__with_common_name():
    taxon = load_sample_data('get_taxa.json')['results'][0]
    expected_str = 'Species: Nicrophorus vespilloides (Lesser Vespillo Burying Beetle)'
    assert format_taxon_str(taxon) == expected_str


def test_format_taxon__without_common_name():
    taxon = load_sample_data('get_taxa.json')['results'][2]
    assert format_taxon_str(taxon) == 'Species: Temnostoma vespiforme'


def test_format_taxon__invalid():
    assert format_taxon_str(None) == 'unknown taxon'


def test_simplify_observation():
    observation = load_sample_data('get_observation.json')['results'][0]
    simplified_obs = simplify_observation(observation)
    # Not much worth testing here, just make sure it returns something that can be formatted
    assert format_observation_str(simplified_obs)
