import pytest
from datetime import datetime
from dateutil.tz import tzoffset

from pyinaturalist.response_format import (
    format_observation,
    format_taxon,
    parse_observation_timestamp,
)
from test.conftest import load_sample_data


def test_format_observation():
    observation = load_sample_data('get_observation.json')['results'][0]
    assert format_observation(observation) == (
        '[16227955] Species: Lixus bardanae '
        'observed by niconoe on 2018-09-05 at 54 rue des Badauds'
    )


def test_format_taxon__with_common_name():
    taxon = load_sample_data('get_taxa.json')['results'][0]
    assert (
        format_taxon(taxon) == 'Species: Nicrophorus vespilloides (Lesser Vespillo Burying Beetle)'
    )


def test_format_taxon__without_common_name():
    taxon = load_sample_data('get_taxa.json')['results'][2]
    assert format_taxon(taxon) == 'Species: Temnostoma vespiforme'


@pytest.mark.parametrize(
    'timestamp, offset_str, expected_date',
    [
        (
            'Sat Sep 26 2020 12:09:51 GMT-0700 (PDT)',
            '-07:00',
            datetime(2020, 9, 26, 12, 9, 51, tzinfo=tzoffset(None, -25200)),
        ),
        (
            '2020-09-27 9:20:02 AM PST',
            'GMT-08:00',
            datetime(2020, 9, 27, 9, 20, 2, tzinfo=tzoffset(None, -28800)),
        ),
        (
            'Dec 04 2020 21:00:00 EET',
            'UTC +02:00',
            datetime(2020, 12, 4, 21, 0, 0, tzinfo=tzoffset(None, 7200)),
        ),
    ],
)
def test_parse_timestamp(timestamp, offset_str, expected_date):
    observation = {'observed_on_string': timestamp, 'time_zone_offset': offset_str}
    parsed_date = parse_observation_timestamp(observation)
    assert parsed_date == expected_date


def test_parse_timestamp__invalid_timestamp():
    observation = {'observed_on_string': 'twelve thirty am yesterday', 'time_zone_offset': '-07:00'}
    assert parse_observation_timestamp(observation) is None


def test_parse_timestamp__invalid_offset():
    observation = {'observed_on_string': '2020-09-27 9:20:02 AM PST', 'time_zone_offset': 'invalid'}
    assert parse_observation_timestamp(observation) is None
