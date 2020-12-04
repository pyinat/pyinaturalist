import pytest
from datetime import datetime
from dateutil.tz import tzoffset

from pyinaturalist.response_format import (
    convert_observation_timestamps,
    convert_offset,
    format_observation,
    format_taxon,
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


def test_format_taxon__invalid():
    assert format_taxon(None) == 'unknown taxon'


@pytest.mark.parametrize(
    'observed_on, created_at, tz_offset, tz_name, expected_observed, expected_created',
    [
        (
            'Sat Sep 26 2020 12:09:51 GMT-0700 (PDT)',
            None,
            '-07:00',
            None,
            datetime(2020, 9, 26, 12, 9, 51, tzinfo=tzoffset(None, -25200)),
            None,
        ),
        (
            '2020-09-27 9:20:02 AM PST',
            '2020-10-01',
            'GMT-08:00',
            'PST',
            datetime(2020, 9, 27, 9, 20, 2, tzinfo=tzoffset('PST', -28800)),
            datetime(2020, 10, 1, tzinfo=tzoffset('PST', -28800)),
        ),
        (
            'Dec 04 2020 21:00:00',
            'Dec 10 2020',
            'UTC +02:00',
            'EET',
            datetime(2020, 12, 4, 21, 0, 0, tzinfo=tzoffset('EET', 7200)),
            datetime(2020, 12, 10, tzinfo=tzoffset('EET', 7200)),
        ),
        (
            None,
            'Dec 10 2020',
            'UTC +02:00',
            'EET',
            None,
            datetime(2020, 12, 10, tzinfo=tzoffset('EET', 7200)),
        ),
    ],
)
def test_convert_observation_timestamps(
    observed_on, created_at, tz_offset, tz_name, expected_observed, expected_created
):
    observation = {
        'created_at_details': {'date': created_at},
        'observed_on_string': observed_on,
        'time_zone_offset': tz_offset,
        'observed_time_zone': tz_name,
    }
    converted = convert_observation_timestamps(observation)
    assert converted['observed_on'] == expected_observed
    assert converted['created_at'] == expected_created


@pytest.mark.parametrize(
    'datetime_obj, tz_offset, tz_name, expected_date',
    [
        (
            datetime(2020, 9, 26, 12, 9, 51),
            '-07:00',
            None,
            datetime(2020, 9, 26, 12, 9, 51, tzinfo=tzoffset(None, -25200)),
        ),
        (
            datetime(2020, 9, 27, 9, 20, 2),
            'GMT-08:00',
            'PST',
            datetime(2020, 9, 27, 9, 20, 2, tzinfo=tzoffset('PST', -28800)),
        ),
        (
            datetime(2020, 12, 4, 21, 0, 0),
            'UTC +02:00',
            'EET',
            datetime(2020, 12, 4, 21, 0, 0, tzinfo=tzoffset('EET', 7200)),
        ),
    ],
)
def test_convert_offset(datetime_obj, tz_offset, tz_name, expected_date):
    assert convert_offset(datetime_obj, tz_offset, tz_name) == expected_date


def test_convert_offset__invalid_offset():
    assert convert_offset(datetime(2020, 1, 1), 'invalid') is None
