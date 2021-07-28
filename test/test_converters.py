from datetime import datetime
from io import BytesIO
from tempfile import NamedTemporaryFile

import pytest
from dateutil.tz import tzoffset

from pyinaturalist.converters import (
    convert_histogram,
    convert_lat_long,
    convert_observation_timestamps,
    convert_offset,
    ensure_file_obj,
    ensure_list,
    format_dimensions,
    format_file_size,
    format_license,
    safe_split,
)
from test.conftest import load_sample_data


@pytest.mark.parametrize(
    'input, expected_output',
    [
        ('1234.5, 6789.0', (1234.5, 6789.0)),
        ({'latitude': 1234.5, 'longitude': 6789.0}, (1234.5, 6789.0)),
        (['1234.5', '6789.0'], (1234.5, 6789.0)),
        ([1234.5, 6789.0], (1234.5, 6789.0)),
        (None, None),
        ('1234.5, 6789.0, 000', None),
        (['1234.5', 'asdf'], None),
        ({'degrees': 12.3}, None),
    ],
)
def test_convert_lat_long(input, expected_output):
    assert convert_lat_long(input) == expected_output


def test_ensure_file_obj__file_path():
    with NamedTemporaryFile() as temp:
        temp.write(b'test content')
        temp.seek(0)

        file_obj = ensure_file_obj(temp.name)
        assert file_obj.read() == b'test content'


def test_ensure_file_obj__file_obj():
    file_obj = BytesIO(b'test content')
    assert ensure_file_obj(file_obj) == file_obj


@pytest.mark.parametrize(
    'input, expected_output',
    [
        (None, []),
        ([], []),
        (1, [1]),
        ('a,b', ['a,b']),
        ({'results': 1}, [1]),
        (tuple([1, 2, 3]), [1, 2, 3]),
    ],
)
def test_ensure_list(input, expected_output):
    assert ensure_list(input) == expected_output


@pytest.mark.parametrize(
    'input, delimiter, expected_output',
    [('a,b', ',', ['a', 'b']), ('a , b', ',', ['a', 'b']), ('a|b', '|', ['a', 'b'])],
)
def test_ensure_list__csv(input, delimiter, expected_output):
    assert ensure_list(input, convert_csv=True, delimiter=delimiter) == expected_output


def test_format_histogram__datetime_keys():
    response = load_sample_data('get_observation_histogram_month.json')
    histogram = convert_histogram(response)
    assert histogram[datetime(2020, 1, 1, 0, 0)] == 272
    assert all([isinstance(k, datetime) for k in histogram.keys()])
    assert all([isinstance(v, int) for v in histogram.values()])


def test_format_histogram__int_keys():
    response = load_sample_data('get_observation_histogram_month_of_year.json')
    histogram = convert_histogram(response)
    assert histogram[1] == 272
    assert all([isinstance(k, int) for k in histogram.keys()])
    assert all([isinstance(v, int) for v in histogram.values()])


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


@pytest.mark.parametrize(
    'input, expected_output',
    [(None, (0, 0)), ((1, 1), (1, 1)), ({"width": 1600, "height": 1200}, (1600, 1200))],
)
def test_format_dimensions(input, expected_output):
    assert format_dimensions(input) == expected_output


@pytest.mark.parametrize(
    'n_bytes, expected_size',
    [
        (None, '0 bytes'),
        (5, '5 bytes'),
        (3 * 1024, '3.00 KB'),
        (1024 * 3000, '2.93 MB'),
        (1024 * 1024 * 5000, '4.88 GB'),
        (1024 * 1024 * 5000 * 1000, '4882.81 GB'),
    ],
)
def test_format_file_size(n_bytes, expected_size):
    assert format_file_size(n_bytes) == expected_size


def test_format_license():
    assert format_license('cc-BY_nC') == 'CC-BY-NC'


@pytest.mark.parametrize('input, expected_output', [(None, []), ('a | b', ['a', 'b'])])
def test_safe_split(input, expected_output):
    assert safe_split(input) == expected_output
