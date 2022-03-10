from datetime import date, datetime, timedelta
from unittest.mock import patch

import pytest
from dateutil.tz import gettz

from pyinaturalist.request_params import (
    convert_bool_params,
    convert_datetime_params,
    convert_list_params,
    convert_observation_field_params,
    convert_pagination_params,
    get_interval_ranges,
    preprocess_request_body,
    preprocess_request_params,
    strip_empty_values,
    validate_ids,
    validate_multiple_choice_param,
    validate_multiple_choice_params,
)

TEST_PARAMS = {
    'is_active': False,
    'only_id': 'true',
    'preferred_place_id': [1, 2],
    'rank': ['phylum', 'class'],
    'q': '',
    'locale': None,
    'parent_id': 1,
    'observation_fields': {1: 'value'},
}


def test_convert_bool_params():
    params = convert_bool_params(TEST_PARAMS)
    assert params['is_active'] == 'false'
    assert params['only_id'] == 'true'


# Test some recognized date(time) formats, with and without TZ info, in date and non-date params
@pytest.mark.parametrize(
    'param, value, expected',
    [
        ('created_d1', '19951231T235959', '1995-12-31T23:59:59-08:00'),
        ('created_d2', '2008-08-08 08:08:08Z', '2008-08-08T08:08:08+00:00'),
        ('created_on', '2010-10-10 10:10:10-05:00', '2010-10-10T10:10:10-05:00'),
        ('created_on', 'Jan 1 2000', '2000-01-01T00:00:00-08:00'),
        ('d1', '19970716', '1997-07-16T00:00:00-07:00'),
        ('q', date(1954, 2, 5), '1954-02-05'),
        ('q', datetime(1954, 2, 5), '1954-02-05T00:00:00-08:00'),
        ('q', 'not a datetime', 'not a datetime'),
    ],
)
@patch('pyinaturalist.converters.tzlocal', return_value=gettz('US/Pacific'))
def test_convert_datetime_params(tzlocal, param, value, expected):
    converted = convert_datetime_params({param: value})
    assert converted[param] == expected


# Test both int and string lists
def test_convert_list_params():
    params = convert_list_params(TEST_PARAMS)
    assert params['preferred_place_id'] == '1,2'
    assert params['rank'] == 'phylum,class'


def test_convert_observation_fields():
    params = convert_observation_field_params(TEST_PARAMS)
    assert params['observation_field_values_attributes'] == [
        {'observation_field_id': 1, 'value': 'value'}
    ]


def test_convert_pagination_params():
    params = convert_pagination_params({'per_page': 100})
    assert params['per_page'] == 100

    params = convert_pagination_params({'per_page': 100, 'count_only': True})
    assert params['per_page'] == 0
    assert 'count_only' not in params

    params = convert_pagination_params({'per_page': 100, 'count_only': False, 'reverse': True})
    assert params['per_page'] == 100
    assert params['order'] == 'descending'
    assert 'reverse' not in params


@pytest.mark.parametrize(
    'start, end, interval',
    [
        (datetime(2020, 1, 1), datetime(2020, 1, 5), 'day'),
        ('2020-01-01', '2020-01-05', 'day'),
        ('2020-01-01', '2020-01-05', timedelta(days=1)),
    ],
)
def test_get_interval_ranges__day(start, end, interval):
    expected_ranges = [
        (datetime(2020, 1, 1, 0, 0), datetime(2020, 1, 1, 23, 59)),
        (datetime(2020, 1, 2, 0, 0), datetime(2020, 1, 2, 23, 59)),
        (datetime(2020, 1, 3, 0, 0), datetime(2020, 1, 3, 23, 59)),
        (datetime(2020, 1, 4, 0, 0), datetime(2020, 1, 4, 23, 59)),
        (datetime(2020, 1, 5, 0, 0), datetime(2020, 1, 5, 23, 59)),
    ]
    ranges = get_interval_ranges(start, end, interval)
    assert ranges == expected_ranges


def test_get_interval_ranges__month():
    expected_ranges = [
        (datetime(2020, 1, 1, 0, 0), datetime(2020, 1, 31, 23, 59)),
        (datetime(2020, 2, 1, 0, 0), datetime(2020, 2, 29, 23, 59)),
        (datetime(2020, 3, 1, 0, 0), datetime(2020, 3, 31, 23, 59)),
        (datetime(2020, 4, 1, 0, 0), datetime(2020, 4, 30, 23, 59)),
        (datetime(2020, 5, 1, 0, 0), datetime(2020, 5, 31, 23, 59)),
        (datetime(2020, 6, 1, 0, 0), datetime(2020, 6, 30, 23, 59)),
        (datetime(2020, 7, 1, 0, 0), datetime(2020, 7, 31, 23, 59)),
        (datetime(2020, 8, 1, 0, 0), datetime(2020, 8, 31, 23, 59)),
        (datetime(2020, 9, 1, 0, 0), datetime(2020, 9, 30, 23, 59)),
        (datetime(2020, 10, 1, 0, 0), datetime(2020, 10, 31, 23, 59)),
        (datetime(2020, 11, 1, 0, 0), datetime(2020, 11, 30, 23, 59)),
        (datetime(2020, 12, 1, 0, 0), datetime(2020, 12, 31, 23, 59)),
    ]
    ranges = get_interval_ranges(datetime(2020, 1, 1), datetime(2020, 12, 31), 'month')
    assert ranges == expected_ranges


def test_get_interval_ranges__year():
    expected_ranges = [
        (datetime(2010, 1, 1, 0, 0), datetime(2010, 12, 31, 23, 59)),
        (datetime(2011, 1, 1, 0, 0), datetime(2011, 12, 31, 23, 59)),
        (datetime(2012, 1, 1, 0, 0), datetime(2012, 12, 31, 23, 59)),
        (datetime(2013, 1, 1, 0, 0), datetime(2013, 12, 31, 23, 59)),
        (datetime(2014, 1, 1, 0, 0), datetime(2014, 12, 31, 23, 59)),
        (datetime(2015, 1, 1, 0, 0), datetime(2015, 12, 31, 23, 59)),
        (datetime(2016, 1, 1, 0, 0), datetime(2016, 12, 31, 23, 59)),
        (datetime(2017, 1, 1, 0, 0), datetime(2017, 12, 31, 23, 59)),
        (datetime(2018, 1, 1, 0, 0), datetime(2018, 12, 31, 23, 59)),
        (datetime(2019, 1, 1, 0, 0), datetime(2019, 12, 31, 23, 59)),
        (datetime(2020, 1, 1, 0, 0), datetime(2020, 12, 31, 23, 59)),
    ]
    ranges = get_interval_ranges(datetime(2010, 1, 1), datetime(2020, 12, 31), 'year')
    assert ranges == expected_ranges


def test_strip_empty_params():
    params = strip_empty_values(TEST_PARAMS)
    assert len(params) == 6
    assert 'q' not in params and 'locale' not in params
    assert 'is_active' in params and 'only_id' in params


@pytest.mark.parametrize(
    'value, expected',
    [
        ('1', '1'),
        (1, '1'),
        ('1,2,3', '1,2,3'),
        ([1, 2, 3], '1,2,3'),
        ([1e5, 2e5], '100000,200000'),
    ],
)
def test_validate_ids(value, expected):
    assert validate_ids(value) == expected


def test_validate_ids__invalid():
    with pytest.raises(ValueError):
        validate_ids('not a number')


# This is just here so that tests will fail if one of the conversion steps is removed
@patch('pyinaturalist.request_params.convert_bool_params')
@patch('pyinaturalist.request_params.convert_datetime_params')
@patch('pyinaturalist.request_params.convert_list_params')
@patch('pyinaturalist.request_params.strip_empty_values')
def test_preprocess_request_params(mock_bool, mock_datetime, mock_list, mock_strip):
    preprocess_request_params({'id': 1})
    assert all([mock_bool.called, mock_datetime.called, mock_list.called, mock_strip.called])


@patch('pyinaturalist.request_params.convert_bool_params')
@patch('pyinaturalist.request_params.convert_datetime_params')
@patch('pyinaturalist.request_params.convert_list_params')
@patch('pyinaturalist.request_params.strip_empty_values')
def test_preprocess_request_body(mock_bool, mock_list, mock_datetime, mock_strip):
    preprocess_request_body({'id': 1})
    assert all([mock_bool.called, mock_datetime.called, not mock_list.called, mock_strip.called])


def test_validate_multiple_choice_param():
    params = {
        'param1': 'valid_str',
        'param2': 'invalid_str',
    }
    choices = ['str1', 'str2', 'valid_str']

    validated_params = validate_multiple_choice_param(params, 'param1', choices)
    assert params == validated_params
    with pytest.raises(ValueError):
        validate_multiple_choice_param(params, 'param2', choices)


@pytest.mark.parametrize(
    'params',
    [
        {'csi': 'LC'},
        {'csi': ['EW', 'EX']},
        {'geoprivacy': 'open'},
        {'iconic_taxa': 'Animalia'},
        {'identifications': 'most_agree'},
        {'license': 'CC-BY-NC'},
        {'rank': 'order'},
        {'quality_grade': 'research'},
        {'search_on': 'tags'},
        {'geoprivacy': ['open', 'obscured']},
        {'geoprivacy': 'open', 'iconic_taxa': 'Animalia', 'license': 'CC-BY-NC'},
    ],
)
def test_validate_multiple_choice_params(params):
    # If valid, no exception should not be raised
    validate_multiple_choice_params(params)

    # If invalid, an exception should be raised
    with pytest.raises(ValueError):
        validate_multiple_choice_params({k: 'Invalid_value' for k in params})

    # A valid + invalid value should also raise an exception
    def append_invalid_value(value):
        return [*value, 'Invalid_value'] if isinstance(value, list) else [value, 'Invalid_value']

    with pytest.raises(ValueError):
        validate_multiple_choice_params({k: append_invalid_value(v) for k, v in params.items()})


@pytest.mark.parametrize(
    'params, expected_value',
    [
        ({'identifications': 'most agree'}, 'most_agree'),
        ({'interval': 'month of year'}, 'month_of_year'),
    ],
)
def test_validate_multiple_choice_params__normalization(params, expected_value):
    validated_params = validate_multiple_choice_params(params)
    value = next(iter(validated_params.values()))
    assert value == expected_value
