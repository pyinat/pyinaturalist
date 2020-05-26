import pytest
from datetime import date, datetime
from dateutil.tz import gettz
from unittest.mock import patch

from pyinaturalist.helpers import (
    preprocess_request_params,
    convert_bool_params,
    convert_datetime_params,
    convert_list_params,
    strip_empty_params,
)


TEST_PARAMS = {
    "is_active": False,
    "only_id": "true",
    "preferred_place_id": [1, 2],
    "rank": ["phylum", "class"],
    "q": "",
    "locale": None,
    "parent_id": 1,
}


def test_convert_bool_params():
    params = convert_bool_params(TEST_PARAMS)
    assert params["is_active"] == "false"
    assert params["only_id"] == "true"


# Test both int and string lists
def test_convert_list_params():
    params = convert_list_params(TEST_PARAMS)
    assert params["preferred_place_id"] == "1,2"
    assert params["rank"] == "phylum,class"


def test_strip_empty_params():
    params = strip_empty_params(TEST_PARAMS)
    assert len(params) == 5
    assert "q" not in params and "locale" not in params
    assert "is_active" in params and "only_id" in params


# Test some recognized date(time) formats, with and without TZ info, in date and non-date params
@pytest.mark.parametrize(
    "param, value, expected",
    [
        ("created_d1", "19951231T235959", "1995-12-31T23:59:59-08:00"),
        ("created_d2", "2008-08-08 08:08:08Z", "2008-08-08T08:08:08+00:00"),
        ("created_on", "2010-10-10 10:10:10-05:00", "2010-10-10T10:10:10-05:00"),
        ("created_on", "Jan 1 2000", "2000-01-01T00:00:00-08:00"),
        ("d1", "19970716", "1997-07-16T00:00:00-07:00"),
        ("q", date(1954, 2, 5), "1954-02-05"),
        ("q", datetime(1954, 2, 5), "1954-02-05T00:00:00-08:00"),
        ("q", "not a datetime", "not a datetime"),
    ],
)
@patch("pyinaturalist.helpers.tzlocal", return_value=gettz("US/Pacific"))
def test_convert_datetime_params(tzlocal, param, value, expected):
    converted = convert_datetime_params({param: value})
    assert converted[param] == expected


# This is just here so that tests will fail if one of the conversion steps is removed
@patch("pyinaturalist.helpers.convert_bool_params")
@patch("pyinaturalist.helpers.convert_datetime_params")
@patch("pyinaturalist.helpers.convert_list_params")
@patch("pyinaturalist.helpers.strip_empty_params")
def test_preprocess_request_params(mock_bool, mock_datetime, mock_list, mock_strip):
    preprocess_request_params({"id": 1})
    assert all(
        [mock_bool.called, mock_datetime.called, mock_list.called, mock_strip.called]
    )
