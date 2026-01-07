import os
from datetime import datetime
from io import BytesIO
from tempfile import NamedTemporaryFile
from unittest.mock import MagicMock

import pytest
from dateutil.tz import tzoffset
from requests import Response
from urllib3 import HTTPResponse

from pyinaturalist.constants import MAX_FILESIZE
from pyinaturalist.converters import (
    convert_lat_long,
    convert_observation_histogram,
    convert_observation_timestamps,
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
        (('1234.5', '6789.0'), (1234.5, 6789.0)),
        ([1234.5, 6789.0], (1234.5, 6789.0)),
        (None, None),
        ('1234.5, 6789.0, 000', None),
        (['1234.5', 'asdf'], None),
        ({'degrees': 12.3}, None),
    ],
)
def test_convert_lat_long(input, expected_output):
    assert convert_lat_long(input) == expected_output


def test_ensure_file_obj__obj():
    file_obj = ensure_file_obj(BytesIO(b'test content'))
    assert file_obj.read() == b'test content'


def test_ensure_file_obj__path():
    with NamedTemporaryFile(delete=False) as temp:
        temp.write(b'test content')
        temp.seek(0)

        file_obj = ensure_file_obj(temp.name)
        assert file_obj.read() == b'test content'
    os.remove(temp.name)


def test_ensure_file_obj__url():
    session = MagicMock()
    response = Response()
    response.raw = HTTPResponse(
        body=BytesIO(b'test content'),
        preload_content=False,
        status=200,
    )
    response.headers = {'Content-Length': '12'}
    response.status_code = 200
    response.encoding = 'utf-8'
    session.get.return_value = response

    file_obj = ensure_file_obj('https://example.com/file.mp3', session)
    assert file_obj.read() == b'test content'


def test_ensure_file_obj__bytes():
    file_obj = ensure_file_obj(b'test content')
    assert file_obj.read() == b'test content'


def test_ensure_file_obj__exceeds_max_filesize():
    contents = b'1' * (MAX_FILESIZE + 1)
    with pytest.raises(ValueError):
        ensure_file_obj(value=contents)


@pytest.mark.parametrize(
    'input, expected_output',
    [
        (None, []),
        ([], []),
        (1, [1]),
        ('a,b', ['a,b']),
        ({'results': 1}, [1]),
        ((1, 2, 3), [1, 2, 3]),
    ],
)
def test_ensure_list(input, expected_output):
    assert ensure_list(input) == expected_output


@pytest.mark.parametrize(
    'input, delimiter, expected_output',
    [('a,b', ',', ['a', 'b']), ('a , b', ',', ['a', 'b']), ('a|b', '|', ['a', 'b'])],
)
def test_ensure_list__csv(input, delimiter, expected_output):
    assert ensure_list(input, split_str_list=True, delimiter=delimiter) == expected_output


def test_format_histogram__datetime_keys():
    response = load_sample_data('get_observation_histogram_month.json')
    histogram = convert_observation_histogram(response)
    assert histogram[datetime(2020, 1, 1, 0, 0)] == 272
    assert all(isinstance(k, datetime) for k in histogram.keys())
    assert all(isinstance(v, int) for v in histogram.values())


def test_format_histogram__int_keys():
    response = load_sample_data('get_observation_histogram_month_of_year.json')
    histogram = convert_observation_histogram(response)
    assert histogram[1] == 272
    assert all(isinstance(k, int) for k in histogram.keys())
    assert all(isinstance(v, int) for v in histogram.values())


@pytest.mark.parametrize(
    'observed_on, created_at, expected_observed, expected_created',
    [
        (
            'Sat Sep 26 2020 12:09:51 -07:00',
            None,
            datetime(2020, 9, 26, 12, 9, 51, tzinfo=tzoffset(None, -25200)),
            None,
        ),
        (
            '2020-09-27T9:20:02-08:00',
            '2020-10-01T00:00-08:00',
            datetime(2020, 9, 27, 9, 20, 2, tzinfo=tzoffset(None, -28800)),
            datetime(2020, 10, 1, tzinfo=tzoffset(None, -28800)),
        ),
        (
            '2020-12-04T21:00+02:00',
            '2020-12-10T00:00+02:00',
            datetime(2020, 12, 4, 21, 0, 0, tzinfo=tzoffset(None, 7200)),
            datetime(2020, 12, 10, tzinfo=tzoffset(None, 7200)),
        ),
        (
            None,
            '2020-12-10T00:00+02:00',
            None,
            datetime(2020, 12, 10, tzinfo=tzoffset(None, 7200)),
        ),
    ],
)
def test_convert_observation_timestamps(
    observed_on, created_at, expected_observed, expected_created
):
    observation = {
        'created_at': created_at,
        'time_observed_at': observed_on,
    }
    converted = convert_observation_timestamps(observation)
    assert converted.get('observed_on') == expected_observed
    assert converted['created_at'] == expected_created


@pytest.mark.parametrize(
    'input, expected_output',
    [(None, (0, 0)), ((1, 1), (1, 1)), ({'width': 1600, 'height': 1200}, (1600, 1200))],
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
